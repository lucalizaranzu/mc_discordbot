import discord
from discord.ext import commands
import logging
import json
import re

from discord.ext.commands import Context
from dotenv import load_dotenv
import os

import bot_rcon
import bot_rcon as brcon
import util

import voice_interaction as vi

from util import requires_custom_permission, updateJSON

#Environment variables
load_dotenv()
token=os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

#Discord intents (perms)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

#Bot instantiation
bot = commands.Bot(command_prefix='!', intents=intents)


server_whitelist = util.readJSON("data/server_whitelist.json")
config = util.readJSON("data/config.json")


# Event handler for when bot is started
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('------')


@bot.command()
async def sendmessage(ctx, *, arg):
    """
    Sends a message to the server
    """
    sender = ctx.author.name

    # Build the JSON structure as Python list/dict
    tellraw_obj = [
        {"text": "[", "color": "white"},
        {"text": sender + " @ Discord", "color": "aqua"},
        {"text": "] ", "color": "white"},
        {"text": arg}
    ]

    #Convert to JSON string (compact)
    tellraw_json = json.dumps(tellraw_obj)

    await brcon.call_mc_command(ctx, f'/tellraw @a {tellraw_json}')

@bot.command()
@requires_custom_permission("administrator", config)
async def mccommand(ctx, *, command):
    """
    Sends a command to the Minecraft server via RCON.
    """
    response = await brcon.call_mc_command(ctx, str(command))
    if response:
        await ctx.send(f"### Executed command: {response}")
    else:
        return


#Creates whitelist command group
@requires_custom_permission("whitelist", config)
@bot.group(invoke_without_command=True)
async def whitelist(ctx):
    """
    Adds or removes users to/from whitelist, or lists
    Usage: !whitelist [add|remove|check|modremove] [username]
    Usage: !whitelist [list|listall]
    """
    await ctx.send("## Available subcommands:\n>>> add\nremove\nlist\nlistall\ncheck\nmodremove") #default

@requires_custom_permission("whitelist", config)
@whitelist.command()
async def add(ctx, arg):
    sender_UUID = str(ctx.author.id)
    print(f"Discord user {ctx.author.name} ({sender_UUID}) requested to whitelist user {arg}")

    if util.is_user_in_whitelist(server_whitelist, arg):
        await ctx.send(f"### User {arg} has already been whitelisted by you or another user")
        return

    if sender_UUID not in server_whitelist:
        server_whitelist[sender_UUID] = []
        print("Added empty whitelist entry for user")

    multiple_whitelist_okay = util.check_user_permissions(ctx, config, "unlimited_whitelist")

    whitelist_user_okay = False
    remove_other_whitelisted_user = False

    if multiple_whitelist_okay: #Case for if user can whitelist multiple users

        if arg not in server_whitelist[sender_UUID]:
            whitelist_user_okay = True
        else:
            await ctx.send(f"### User {arg} is already whitelisted.")
            return

    else: #Case for if user can only whitelist one user
        print("User does not have moderator role, allowing only one whitelist entry.")

        currently_whitelisted = server_whitelist[sender_UUID][0] if server_whitelist.get(sender_UUID) else None

        if arg == currently_whitelisted:
            await ctx.send(f"### User {arg} is already whitelisted.")
            return

        if currently_whitelisted:
            remove_other_whitelisted_user = True

        whitelist_user_okay = True


    if remove_other_whitelisted_user:

        currently_whitelisted = server_whitelist[sender_UUID][0] #Already did checks so we can avoid here

        result = await brcon.call_mc_command(ctx, f"/whitelist remove {currently_whitelisted}")

        if not result:
            return

        server_whitelist[sender_UUID].remove(currently_whitelisted)
        await ctx.send(f"### Removed {currently_whitelisted} from your whitelist")

    if whitelist_user_okay:
        result = await brcon.call_mc_command(ctx, f"/whitelist add {arg}")

        if "That player does not exist" in result:
            await ctx.send(f"### Player `{arg}` does not exist. Make sure the username is correct.")
            return

        if not result:
            return

        server_whitelist[sender_UUID].append(arg)

        await ctx.send(f"### User {arg} has been added to your whitelist.")

    util.updateJSON("data/server_whitelist.json", server_whitelist)

@requires_custom_permission("whitelist", config)
@whitelist.command()
async def remove(ctx, arg):
    sender_UUID = str(ctx.author.id)
    print(f"Discord user {ctx.author.name} ({sender_UUID}) requested to remove whitelist user {arg}")

    if sender_UUID not in server_whitelist or arg not in server_whitelist[sender_UUID]:
        await ctx.send(f"### User {arg} is not in your whitelist.")
        return

    result = await brcon.call_mc_command(ctx, f"/whitelist remove {arg}")

    if not result:
        return

    if "That player does not exist" in result:
        await ctx.send(f"### Player `{arg}` does not exist. Make sure the username is correct.")
        return

    server_whitelist[sender_UUID].remove(arg)
    await ctx.send(f"### User {arg} has been removed from your whitelist.")

    util.updateJSON("data/server_whitelist.json", server_whitelist)

@whitelist.command()
async def list(ctx):
    """
    Displays the current user's whitelisted user(s).
    """
    sender_UUID = str(ctx.author.id)

    if sender_UUID in server_whitelist and server_whitelist[sender_UUID]:

        whitelisted_users = f"## {ctx.author.mention}'s whitelisted user(s):\n>>> "

        for user in server_whitelist[sender_UUID]:
            whitelisted_users += f"{user}\n"

        await ctx.send(whitelisted_users,
                       allowed_mentions=discord.AllowedMentions(roles=False)) #Disable mentions
    else:
        await ctx.send("### You have not whitelisted any users.")


@whitelist.command()
@requires_custom_permission("moderator", config)
async def modremove(ctx, username: str):
    """
    Removes any whitelisted users from the whitelist, even if you did not personally whitelist them
    """

    all_user_whitelists = [user for user in server_whitelist]

    if not all_user_whitelists:
        await ctx.send("### There are no whitelisted users on this server.")
        return


    for user_whitelist in all_user_whitelists:
        if username in server_whitelist.get(user_whitelist):
            result = await brcon.call_mc_command(ctx, f"/whitelist remove {username}")

            if not result:
                return

            if "That player does not exist" in result:
                await ctx.send(f"### Player `{username}` does not exist. Make sure the username is correct.")
                return

            whitelist_username = bot.get_user(int(user_whitelist)).mention
            if not whitelist_username:
                whitelist_username = user_whitelist

            server_whitelist[user_whitelist].remove(username)
            await ctx.send(f"### {username} has been removed from {whitelist_username}'s whitelist.\n",
                           allowed_mentions=discord.AllowedMentions(roles=False)) #Disable mentions)

            #Save changes
            server_whitelist[user_whitelist].remove(username)
            util.updateJSON("data/server_whitelist.json", server_whitelist)

            return

    await ctx.send(f"### User {username} is not whitelisted on this server.")

@whitelist.command()
async def listall(ctx):
    """
    Displays the current user's whitelisted user.
    """

    all_users = [user for users in server_whitelist.values() for user in users]

    if not all_users:
        await ctx.send("### There are no whitelisted users on this server.")
        return

    whitelisted_users = f"## This server's whitelist currently includes:\n>>> "

    for user in all_users:
        whitelisted_users += f"{user}\n"

    await ctx.send(whitelisted_users)

@whitelist.command()
async def check(ctx, username):
    """
    Checks if a user is whitelisted
    """

    if util.is_user_in_whitelist(server_whitelist, username):
        await ctx.send(f"### User {username} is whitelisted.")
        return
    await ctx.send(f"### User {username} is not whitelisted.")


#Role permissions

@requires_custom_permission("administrator", config) #only admin can edit role permissions
@bot.group(invoke_without_command=True)
async def rolepermission(ctx):
    """
    Adds or removes custom permissions from a server role
    Usage: !rolepermission [add|remove|list] [role] [permission]
    """
    await ctx.send("## Available subcommands:\n>>> add\nremove\nlist") #default

@requires_custom_permission("administrator", config) #only admin can edit role permissions
@rolepermission.command()
async def add(ctx, role: discord.Role, permission: str):

    if not isinstance(role, discord.Role):
        await ctx.send("### Invalid role provided.")
        return

    if permission not in config["existing_permissions"]:
        await ctx.send(f"### Permission '{permission}' is not a valid permission.")
        return

    role_id_str = str(role.id)
    role_permissions = config["role_permissions"].get(role_id_str)

    if not role_permissions:
        role_permissions = []

    if permission in role.permissions:
        await ctx.send(f"### Permission '{permission}' already exists for role '{role.name}'.")
        return

    role_permissions.append(permission)
    await ctx.send(f"### Permission '{permission}' added to '{role}'.")

    config["role_permissions"][role_id_str] = role_permissions
    util.updateJSON("data/config.json", config)

@requires_custom_permission("administrator", config) #only admin can edit role permissions
@rolepermission.command()
async def remove(ctx, role: discord.Role, permission):
    """
    Removes a permission from a role.
    """
    if not isinstance(role, discord.Role):
        await ctx.send("### Invalid role provided.")
        return

    role_id_str = str(role.id)
    role_permissions = config['role_permissions'].get(role_id_str)

    if not role_permissions:
        await ctx.send(f"### Role '{role.name}' has no permissions to remove")
        return

    if permission not in config['role_permissions'][role_id_str]:
        await ctx.send(f"### Permission '{permission}' not found for role '{role.name}'.")
        return

    role_permissions.remove(permission)
    await ctx.send(f"### Permission '{permission}' removed for role '{role.name}'.")

    config["role_permissions"][role_id_str] = role_permissions
    util.updateJSON("data/config.json", config)


@requires_custom_permission("administrator", config) #only admin can edit role permissions
@rolepermission.command()
async def list(ctx, role: discord.Role):
    """
    Displays the current user's whitelisted user.
    """

    if not isinstance(role, discord.Role):
        await ctx.send("Invalid role provided.")
        return

    role_permissions = f"## Permissions for role '{role.name}':\n>>> "

    rolestr = str(role.id)

    if rolestr in config['role_permissions'] and config['role_permissions'][rolestr]:
        for permission in set(config['role_permissions'].get(rolestr, [])):
            role_permissions += f"{permission}\n"

        await ctx.send(role_permissions)
    else:
        await ctx.send("### Role does not have any permissions")


@bot.command()
async def listplayers(ctx):
    """
    Lists all currently online players
    """
    output = await bot_rcon.call_mc_command(ctx, f"/list")

    if not output:
        return

    players = []

    match = re.search(r'online:\s(.+)', output)
    if match:
        players = [p.strip() for p in match.group(1).split(',')]

    if not players:
        await ctx.send("There are no players currently online.")
        return
    await ctx.send(f"## Players currently online:\n>>> " + '\n'.join(players))



@bot.command()
async def hh(ctx, arg = None):

    if arg == "stop":
        await vi.stop_playing_sound(ctx)
        return

    print("Playing hh sound")
    hh_path = "assets/hh.mp3"

    if not ctx.voice_client:
        print("No voice client detected")

    await vi.play_sound_in_channel(config, ctx, hh_path)

@bot.command()
async def disconnect(ctx):
    """
    Disconnects the bot from the voice channel
    """
    await vi.leave_voice_channel(ctx)

#Run bot
bot.run(token, log_handler = handler, log_level=logging.DEBUG)