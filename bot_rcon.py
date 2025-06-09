from mcrcon import MCRcon, MCRconException
from dotenv import load_dotenv
import asyncio
import os

# Load environment variables
load_dotenv()

rcon_password = os.getenv('RCON_PASSWORD')
RCON_HOST = "192.168.50.114"
RCON_PORT = 25575

async def call_mc_command(command: str) -> str | None:
    def run_rcon_command():
        try:
            with MCRcon(RCON_HOST, rcon_password, port=RCON_PORT) as mcr:
                return mcr.command(command)
        except Exception as e:
            print(f"[RCON Error] Failed to run command '{command}': {e}")
            return None

    return await asyncio.to_thread(run_rcon_command)