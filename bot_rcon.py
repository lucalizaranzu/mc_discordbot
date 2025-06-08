from mcrcon import MCRcon, MCRconException
from dotenv import load_dotenv
import asyncio
import os

#Environment variables
load_dotenv()

rcon_password = os.getenv('RCON_PASSWORD')

#RCON
RCON_HOST = "192.168.50.114"
RCON_PORT = 25575

async def call_mc_command(command: str) -> str | None:
    loop = asyncio.get_event_loop()

    def run_rcon_command():
        try:
            with MCRcon(RCON_HOST, rcon_password, port=RCON_PORT) as mcr:
                return mcr.command(command)
        except Exception as e:
            print(f"[RCON Error] Failed to run command '{command}': {e}")
            return None

    return await loop.run_in_executor(None, run_rcon_command)
