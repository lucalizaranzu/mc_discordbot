import discord
from typing import cast

from util import util as ut
from commands.commands_base import custom_command, has_permission
from bot import global_bot
from util import server as sv

from util import bot_rcon as brcon



#Creates whitelist command group
@global_bot.group(invoke_without_command=True)
async def whitelist(ctx):
    """
    Adds or removes users to/from whitelist, or lists
    Usage: !whitelist [add|remove|check|modremove] [username]
    Usage: !whitelist [list|listall]
    """
    await ctx.send("## Available subcommands:\n>>> add\nremove\nlist\nlistall\ncheck\nmodremove") #default

@custom_command("whitelist")
@whitelist.command()
async def add(ctx, arg):

    sender_server = cast(sv.Server, ctx.server)

    server_whitelist = sender_server.get_whitelist()
    server_config = sender_server.get_config()

    sender_UUID = str(ctx.author.id)
    print(f"Discord user {ctx.author.name} ({sender_UUID}) requested to whitelist user {arg}")

    if ut.is_user_in_whitelist(server_whitelist, arg):
        await ctx.send(f"### User {arg} has already been whitelisted by you or another user")
        return

    if sender_UUID not in server_whitelist:
        server_whitelist[sender_UUID] = []
        print("Added empty whitelist entry for user")

    multiple_whitelist_okay = has_permission(ctx, server_config, "unlimited_whitelist")

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

    sender_server.update_whitelist()

@custom_command("whitelist")
@whitelist.command()
async def remove(ctx, arg):

    sender_server = cast(sv.Server, ctx.server)

    server_whitelist = sender_server.get_whitelist()

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

    sender_server.update_whitelist()

@whitelist.command()
@custom_command("whitelist")
async def list(ctx):
    """
    Displays the current user's whitelisted user(s).
    """

    sender_server = cast(sv.Server, ctx.server)

    server_whitelist = sender_server.get_whitelist()

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
@custom_command("administrator")
async def modremove(ctx, username: str):
    """
    Removes any whitelisted users from the whitelist, even if you did not personally whitelist them
    """

    sender_server = cast(sv.Server, ctx.server)

    server_whitelist = sender_server.get_whitelist()

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

            whitelist_username = global_bot.get_user(int(user_whitelist)).mention
            if not whitelist_username:
                whitelist_username = user_whitelist

            server_whitelist[user_whitelist].remove(username)
            await ctx.send(f"### {username} has been removed from {whitelist_username}'s whitelist.\n",
                           allowed_mentions=discord.AllowedMentions(roles=False)) #Disable mentions)

            #Save changes
            server_whitelist[user_whitelist].remove(username)
            sender_server.update_whitelist()

            return

    await ctx.send(f"### User {username} is not whitelisted on this server.")

@whitelist.command()
@custom_command()
async def listall(ctx):
    """
    Displays the current user's whitelisted user.
    """

    sender_server = cast(sv.Server, ctx.server)

    server_whitelist = sender_server.get_whitelist()

    all_users = [user for users in server_whitelist.values() for user in users]

    if not all_users:
        await ctx.send("### There are no whitelisted users on this server.")
        return

    whitelisted_users = f"## This server's whitelist currently includes:\n>>> "

    for user in all_users:
        whitelisted_users += f"{user}\n"

    await ctx.send(whitelisted_users)

@whitelist.command()
@custom_command()
async def check(ctx, username):
    """
    Checks if a user is whitelisted
    """

    sender_server = cast(sv.Server, ctx.server)

    server_whitelist = sender_server.get_whitelist()

    if ut.is_user_in_whitelist(server_whitelist, username):
        await ctx.send(f"### User {username} is whitelisted.")
        return
    await ctx.send(f"### User {username} is not whitelisted.")
