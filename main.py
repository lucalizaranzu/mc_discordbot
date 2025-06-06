import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

import bot_rcon

#Environment variables
load_dotenv()
token=os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

#Discord intents (perms)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True



#Bot instantiation
bot = commands.Bot(command_prefix='!', intents=intents)



# Event handler for when bot is started
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('------')

@bot.command()
async def setserverdirectory(ctx, arg):
    os.environ['SERVER_DIRECTORY'] = '/home/test_server'
    await ctx.send(f'Server directory set to: {os.environ["SERVER_DIRECTORY"]}')

@bot.command()
async def sendServerMessage(ctx, arg):
    result = await bot_rcon.sendServerMessage(arg)
    if result:
        await ctx.send(f"Message sent to server: {arg}")
    else:
        await ctx.send("Failed to send message.")




#Run bot
bot.run(token, log_handler = handler, log_level=logging.DEBUG)