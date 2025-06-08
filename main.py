import discord
from discord.ext import commands
import logging
import json

from discord.ext.commands import Context
from dotenv import load_dotenv
import os

import bot_rcon as brcon
import util

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

    await brcon.call_mc_command(f'/tellraw @a {tellraw_json}')

@bot.command()
@util.requires_roles_from_config("admin_roles", config)
async def mccommand(ctx, *, command):
    """
    Sends a command to the Minecraft server via RCON.
    """
    response = await brcon.call_mc_command(str(command))
    if response:
        await ctx.send(f"Executed command: {response}")
    else:
        await ctx.send("Failed to execute command.")


@bot.command()
@util.requires_roles_from_config("moderator_roles", config)
async def addmoderatorrole(ctx, role: discord.Role):
    """
    Adds a role to the list of moderator roles.
    Usage: !addmoderatorrole @mod
    """
    mod_roles = config.get('moderator_roles', [])

    if role.id in mod_roles:
        await ctx.send(f"Role '{role.name}' is already a moderator role.")
        return

    mod_roles.append(role.id)
    config['moderator_roles'] = mod_roles
    util.updateJSON("data/config.json", config)

    await ctx.send(f"Role '{role.name}' added to moderator roles.")

@bot.command()
@util.requires_roles_from_config("admin_roles", config)
async def addadminrole(ctx, role: discord.Role):
    """
    Adds a role to the list of moderator roles.
    Usage: !addadminrole @admin
    """

    if ctx.author.guild_permissions.administrator:
        admin_roles = config.get('admin_roles', [])

        if role.id in admin_roles:
            await ctx.send(f"Role '{role.name}' is already an admin role.")
            return

        admin_roles.append(role.id)
        config['admin_roles'] = admin_roles
        util.updateJSON("data/config.json", config)

        await ctx.send(f"Role '{role.name}' added to admin roles.")
    else:
        await ctx.send("You do not have permission to add admin roles.")

#Creates whitelist command group
@bot.group(invoke_without_command=True)
async def whitelist(ctx):
    """
    Adds or removes users to/from whitelist, or lists
    Usage: !whitelist [add|remove|list] [username]
    """
    await ctx.send("Available subcommands:\n>>> add\nremove\nlist") #default

@whitelist.command()
async def add(ctx, arg):
    sender_UUID = str(ctx.author.id)
    print(f"Discord user {ctx.author.name} ({sender_UUID}) requested to whitelist user {arg}")

    if sender_UUID not in server_whitelist:
        server_whitelist[sender_UUID] = []
        print("Added empty whitelist entry for user")

    is_mod = util.checkRoles(ctx, config, "moderator_roles") or util.checkRoles(ctx, config, "admin_roles")

    if is_mod:
        print("User has moderator role, allowing multiple whitelist entries.")

        if arg not in server_whitelist[sender_UUID]:
            await brcon.call_mc_command(f"/whitelist add {arg}")
            server_whitelist[sender_UUID].append(arg)
            await ctx.send(f"User {arg} has been whitelisted.")
        else:
            await ctx.send(f"User {arg} is already whitelisted.")
    else:
        print("User does not have moderator role, allowing only one whitelist entry.")

        currently_whitelisted = server_whitelist[sender_UUID][0] if server_whitelist.get(sender_UUID) else None

        if arg == currently_whitelisted:
            await ctx.send(f"User {arg} is already whitelisted.")
            return

        if currently_whitelisted:
            await brcon.call_mc_command(f"/whitelist remove {currently_whitelisted}")
            print(f"Removed {currently_whitelisted} from whitelist.")

        print(f"Whitelisting user {arg}")
        await brcon.call_mc_command(f"/whitelist add {arg}")
        server_whitelist[sender_UUID] = [arg]

        msg = f"User {arg} has been whitelisted."
        if currently_whitelisted:
            msg += f" User {currently_whitelisted} has been removed."

        await ctx.send(msg)

    util.updateJSON("data/server_whitelist.json", server_whitelist)

@whitelist.command()
async def remove(ctx, arg):
    sender_UUID = str(ctx.author.id)
    print(f"Discord user {ctx.author.name} ({sender_UUID}) requested to remove whitelist user {arg}")

    if sender_UUID not in server_whitelist or arg not in server_whitelist[sender_UUID]:
        await ctx.send(f"User {arg} is not in your whitelist.")
        return

    await brcon.call_mc_command(f"/whitelist remove {arg}")
    server_whitelist[sender_UUID].remove(arg)
    await ctx.send(f"User {arg} has been removed from your whitelist.")

    util.updateJSON("data/server_whitelist.json", server_whitelist)

@whitelist.command()
async def list(ctx):
    """
    Displays the current user's whitelisted user.
    """
    sender_UUID = str(ctx.author.id)

    if sender_UUID in server_whitelist and server_whitelist[sender_UUID]:

        whitelisted_users = f"{ctx.author.mention}'s whitelisted user(s):\n>>> "

        for user in server_whitelist[sender_UUID]:
            whitelisted_users += f"{user}\n"

        await ctx.send(whitelisted_users)
    else:
        await ctx.send("You have not whitelisted any users.")



#Run bot
bot.run(token, log_handler = handler, log_level=logging.DEBUG)