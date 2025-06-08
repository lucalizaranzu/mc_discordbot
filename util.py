import json

from discord.ext.commands import CheckFailure
from discord.ext import commands

def readJSON(file_path):

    with open(file_path, "r") as f:
        try:
            data = json.load(f)
            if not data:
                print("JSON is empty ({} or [])")
                return data
            else:
                return data
        except json.JSONDecodeError:
            print("Invalid or empty JSON file")
            return {}

def updateJSON(file_path : str, json_data : dict):

    with open(file_path, "w") as file:
        json.dump(json_data, file, indent=4)


def requires_roles_from_config(key, cfg):
    async def predicate(ctx):
        allowed_roles = set(cfg.get(key, []))
        user_roles = {role.id for role in ctx.author.roles}
        if user_roles & allowed_roles or ctx.author.guild_permissions.administrator: #Admins bypass
            return True
        raise commands.CheckFailure("You do not have permission.")
    return commands.check(predicate)

def checkRoles(ctx, cfg, allowed_roles):

    sender_roles = {role.id for role in ctx.author.roles}

    allowed_roles_set = set(cfg[allowed_roles])

    has_role = not sender_roles.isdisjoint(allowed_roles_set)

    return has_role or ctx.author.guild_permissions.administrator  #Allow admins to bypass role checks