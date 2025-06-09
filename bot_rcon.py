from mcrcon import MCRcon, MCRconException
from dotenv import load_dotenv
import asyncio
import os
import socket

# Load environment variables
load_dotenv()

rcon_password = os.getenv('RCON_PASSWORD')
RCON_HOST = "192.168.50.114"
RCON_PORT = 25575

async def call_mc_command(ctx, command: str) -> str | None:
    thrown_error = False
    error_string = ""

    def run_rcon_command():
        nonlocal thrown_error, error_string
        try:
            with MCRcon(RCON_HOST, rcon_password, port=RCON_PORT) as mcr:
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
