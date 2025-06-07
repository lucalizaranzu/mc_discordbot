from mcrcon import MCRcon, MCRconException
from dotenv import load_dotenv
import os

#Environment variables
load_dotenv()

rcon_password = os.getenv('RCON_PASSWORD')

#RCON
RCON_HOST = "localhost"
RCON_PORT = 25575

def sendServerMessage(message):
    try:
        with MCRcon(RCON_HOST, rcon_password, port=RCON_PORT) as mcr:
            print("Attempting to send message...")
            return mcr.command(f"/say {message}")
    except Exception as e:
        print(f"Failed to send message via RCON: {e}")
        return None

def whitelistUser(player):
    try:
        with MCRcon(RCON_HOST, rcon_password, port=RCON_PORT) as mcr:
            print("Attempting to whitelist user...")
            return mcr.command(f"/whitelist {player}")
    except Exception as e:
        print(f"Failed to whitelist via RCON: {e}")
        return None