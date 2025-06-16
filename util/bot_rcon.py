from mcrcon import MCRcon, MCRconException
from dotenv import load_dotenv
import asyncio
import os
import socket

from . import util as ut

# Load environment variables
load_dotenv()

async def call_mc_command(ctx, command: str) -> str | None:
    thrown_error = False
    error_string = ""

    user_server_config = ut.readJSON(f"data/config/{ctx.guild.id}.json")

    rcon_ip = user_server_config.get("mcserver_ip", "")
    if not rcon_ip:
        await ctx.send("### No Minecraft server IP configured. Set it with !serverip.")
        return None

    rcon_port = user_server_config.get("rcon_port", 25575)

    rcon_password = user_server_config.get("rcon_password", "")

    print("Running command:", command)

    def run_rcon_command():
        nonlocal thrown_error, error_string
        try:
            with MCRcon(rcon_ip, rcon_password, port=rcon_port) as mcr:
                return mcr.command(command)
        except ConnectionRefusedError as e:
            if e.errno == 10061:  #WinError 10061, server offline
                thrown_error = True
                error_string = "Server is unreachable or offline!"
            else:
                thrown_error = True
                error_string = f"Connection refused: {e}"
            return None
        except socket.timeout as e:
            thrown_error = True
            error_string = "Server is unreachable or offline!"
            return None
        except Exception as e:
            thrown_error = True
            error_string = f"Unexpected error: {e}"
            return None

    result = await asyncio.to_thread(run_rcon_command)

    if thrown_error:
        await ctx.send(f"Failed to run command: {error_string}")
        print("Failed")
        return None

    return result
