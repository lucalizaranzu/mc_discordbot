import discord
from discord.ext import commands

import util.server as sv
import util.util as ut

#Decorator - change to use for everything
def custom_command(*permissions):

    async def predicate(ctx: discord.ext.commands.Context):
        print("0")
        try:
            server = sv.get_server(ctx.guild.id)
        except Exception:
            print("No server associated with your guild! Run !reloadserver to fix!")
            await ctx.send("### No server associated with your guild! Run `!reloadserver` to fix!")
            raise commands.CheckFailure("No server config.")

        ctx.server = server

        if check_user_permissions(ctx, server.get_config(), permissions):
            return True

        await ctx.send(f"### You do not have the required permission: {permissions}")
        raise commands.CheckFailure("You do not have permission.")

    return commands.check(predicate)

def check_user_permissions(ctx: discord.ext.commands.Context, cfg, permissions):
    if ctx.author.guild_permissions.administrator:
        return True

    existing_permissions = set(cfg.get('existing_permissions', []))
    sender_roles = {role for role in ctx.author.roles}

    for perm in permissions:
        if perm not in existing_permissions:
            print(f"Permission '{perm}' does not exist in config.")
            continue

        for role in sender_roles:
            role_permissions = ut.get_role_permissions(cfg, role)
            if perm in role_permissions:
                print(f"Permission '{perm}' granted.")
                return True

    return False

def add_user_role(member : discord.Member, role : discord.Role):
    """
    Gives a Member a role
    """

    if role not in member.roles:
        member.add_roles(role, member)
        return True

    return False