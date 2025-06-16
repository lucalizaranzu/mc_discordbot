import discord
from discord.ext import commands

import util.server as sv
import util.util as ut

#Decorator - change to use for everything
def custom_command(*permission: str):
    def decorator(func):
        @commands.check
        async def predicate(ctx: commands.Context):
            print(f"[DEBUG] Required permissions: {permission}")

            try:
                server = sv.get_server(ctx.guild.id)
            except Exception:
                msg = "### No server associated with your guild! Run `!reloadserver` to fix!"
                print(msg)
                await ctx.send(msg)
                raise commands.CheckFailure("No server config.")

            ctx.server = server
            cfg = server.get_config()

            if all(has_permission(ctx, cfg, perm) for perm in permission):
                return True

            await ctx.send("### You do not have the required permission(s): " + ", ".join(permission))
            raise commands.CheckFailure("Missing permission.")

        return predicate(func)  # Automatically apply decorator
    return decorator

def has_permission(ctx: commands.Context, cfg, permission: str) -> bool:
    # Admin bypass
    if ctx.author.guild_permissions.administrator:
        print("[DEBUG] User has admin permission, bypassing checks.")
        return True

    global_config = ut.readJSON("data/global_config.json")

    role_ids = [str(role.id) for role in ctx.author.roles]
    existing_permissions = set(global_config.get('existing_permissions', []))

    if permission not in existing_permissions:
        print(f"[DEBUG] Permission '{permission}' not in existing_permissions.")
        return False

    for role_id in role_ids:
        role_perms = ut.get_role_permissions(cfg, role_id)
        print(f"[DEBUG] Role {role_id} permissions: {role_perms}")
        if permission in role_perms:
            print(f"[DEBUG] Permission '{permission}' granted by role {role_id}.")
            return True

    print(f"[DEBUG] Permission '{permission}' not granted by any role.")
    return False

def add_user_role(member : discord.Member, role : discord.Role):
    """
    Gives a Member a role
    """

    if role not in member.roles:
        member.add_roles(role, member)
        return True

    return False