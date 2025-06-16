import discord

from typing import cast

from commands.commands_base import custom_command

import bot
from bot import global_bot
from util import server as sv

@custom_command("administrator") #only admin can edit role permissions
@global_bot.group(invoke_without_command=True)
async def rolepermission(ctx):
    """
    Adds or removes custom permissions from a server role
    Usage: !rolepermission [add|remove|list] [role] [permission]
    """
    await ctx.send("## Available subcommands:\n>>> add\nremove\nlist") #default

@custom_command("administrator") #only admin can edit role permissions
@rolepermission.command()
async def add(ctx, role: discord.Role, permission: str):
    """
    Adds a custom permission to a server role
    """

    sender_server = cast(sv.Server, ctx.server)

    server_config = sender_server.get_config()

    if not isinstance(role, discord.Role):
        await ctx.send("### Invalid role provided.")
        return

    if permission not in bot.global_config["existing_permissions"]:
        await ctx.send(f"### Permission '{permission}' is not a valid permission.")
        return

    role_id_str = str(role.id)
    role_permissions = server_config["role_permissions"].get(role_id_str)

    if not role_permissions:
        role_permissions = []

    if permission in role.permissions:
        await ctx.send(f"### Permission '{permission}' already exists for role '{role.name}'.")
        return

    role_permissions.append(permission)
    await ctx.send(f"### Permission '{permission}' added to '{role}'.")

    server_config["role_permissions"][role_id_str] = role_permissions
    sender_server.update_config()
    print(sender_server.get_config()["role_permissions"])
    print("Done")

@custom_command("administrator") #only admin can edit role permissions
@rolepermission.command()
async def remove(ctx, role: discord.Role, permission):
    """
    Removes a permission from a role.
    """

    sender_server = cast(sv.Server, ctx.server)

    server_config = sender_server.get_config()

    if not isinstance(role, discord.Role):
        await ctx.send("### Invalid role provided.")
        return

    role_id_str = str(role.id)
    role_permissions = server_config['role_permissions'].get(role_id_str)

    if not role_permissions:
        await ctx.send(f"### Role '{role.name}' has no permissions to remove")
        return

    if permission not in server_config['role_permissions'][role_id_str]:
        await ctx.send(f"### Permission '{permission}' not found for role '{role.name}'.")
        return

    role_permissions.remove(permission)
    await ctx.send(f"### Permission '{permission}' removed for role '{role.name}'.")

    server_config["role_permissions"][role_id_str] = role_permissions
    sender_server.update_config()


@custom_command("administrator") #only admin can edit role permissions
@rolepermission.command()
async def list(ctx, role: discord.Role):
    """
    Displays the current user's whitelisted user.
    """

    sender_server = cast(sv.Server, ctx.server)

    server_config = sender_server.get_config()

    if not isinstance(role, discord.Role):
        await ctx.send("Invalid role provided.")
        return

    role_permissions = f"## Permissions for role '{role.name}':\n>>> "

    rolestr = str(role.id)

    if rolestr in server_config['role_permissions']:
        for permission in set(server_config['role_permissions'].get(rolestr, [])):
            role_permissions += f"{permission}\n"

        await ctx.send(role_permissions)
    else:
        await ctx.send("### Role does not have any permissions")