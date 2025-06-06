from mcrcon import MCRcon, MCRconException
from dotenv import load_dotenv
import os

#Environment variables
load_dotenv()

rcon_password = os.getenv('RCON_PASSWORD')

#RCON
RCON_HOST = "localhost"
RCON_PORT = 25575

mcr = None

def ensure_connection():
    global mcr
    try:
        if mcr is None:
            mcr = MCRcon(RCON_HOST, rcon_password, port=RCON_PORT)
            mcr.connect()
        elif not mcr.socket:
            mcr.connect()
    except MCRconException as e:
        print("RCON connection failed:", e)
        mcr = None


def sendServerMessage(message):
    ensure_connection()
    if mcr:
        try:
            return mcr.command(f"/say {message}")
        except Exception as e:
            print(f"Failed to send message via RCON: {e}")
            return None
    return None
