import json
import os
import platform
from dotenv import load_dotenv


load_dotenv()

def readJSON(file_path):
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
            if not data:
                print(f"JSON is empty, trying to read {file_path}")
                return data
            else:
                return data
        except json.JSONDecodeError:
            print("Invalid or empty JSON file")
            return {}

def updateJSON(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)



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

def get_program_path(program):

    platform_name = platform.system()

    print(f"Getting program path for {program} on platform {platform_name}")

    program_path = None

    try:
        if platform_name == "Linux":
            program_path = os.getenv(f"{program}_LINUX")
        elif platform_name == "Windows":
            program_path = os.getenv(f"{program}_WINDOWS")
    except KeyError:
        print("Program invalid")
        return None

    return program_path

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
