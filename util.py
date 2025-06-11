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

def updateJSON(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def requires_custom_permission(permission, cfg):

    async def predicate(ctx):
        if check_user_permissions(ctx, cfg, permission):
            return True
        await ctx.send(f"### You do not have the required permission: {permission}")
        raise commands.CheckFailure("You do not have permission.")
    return commands.check(predicate)

def check_user_permissions(ctx, cfg, permission):

    if permission not in cfg.get('existing_permissions', []):
        print(f"Permission '{permission}' does not exist in config.")
        return False

    #if ctx.author.guild_permissions.administrator: #Administrator has all permissions
        #return True

    sender_roles = {role for role in ctx.author.roles}

    for role in sender_roles:
        role_permissions = get_role_permissions(cfg, role)
        if permission in role_permissions:
            print("Permission Granted")
            return True

    return False

def get_role_permissions(cfg, role):
    """
    Returns a set of permissions for a given role based on the config.
    """
    role_permissions = cfg.get('role_permissions', {})
    return set(role_permissions.get(str(role.id), []))

def is_user_in_whitelist(data, username):
    for users in data.values():
        if username in users:
            return True
    return False

def get_program_path(config, platform, program):
    prog_map = config.get("program_locations", {})
    if program not in prog_map:
        print(f"Program '{program}' not found in config.")
        return None

    platform_paths = prog_map[program]
    if platform not in platform_paths:
        print(f"Platform '{platform}' not found for program '{program}'.")
        return None

    return platform_paths[platform]

def check_program_path(path):
    import subprocess

    try:
        result = subprocess.run([path, "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            print(f"Program at path '{path}' returned an error:\n{result.stderr}")
            return False
    except FileNotFoundError:
        print(f"Program at path '{path}' not found")
        return False
    except Exception as e:
        print(f"Unexpected error while checking '{path}': {e}")
        return False

