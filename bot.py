import discord
import logging
from discord.ext import commands
from dotenv import load_dotenv
import os

from util import util as ut

#Environment variables
load_dotenv()
token=os.getenv('DISCORD_TOKEN')

global_config = ut.readJSON("data/global_config.json")

intents = discord.Intents.default()

#Discord intents (perms)
intents.message_content = True
intents.members = True
intents.guilds = True

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')


#Bot instantiation
global_bot = commands.Bot(command_prefix='!', intents=intents)


def run_bot():
    global_bot.run(token, log_handler=handler, log_level=logging.DEBUG)