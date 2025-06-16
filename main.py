import discord
import json
import re
from typing import cast

import bot
from bot import global_bot

from commands import rolepermission, whitelist
from commands import commands_base as cb

import util.voice_interaction as vi
import util.bot_rcon as brcon
import util.server as sv
import os

# Event handler for when bot is started
@global_bot.command()
async def botstatus(ctx):
    """Check bot voice status"""
    print("=== BOT STATUS ===")
    print(f"Voice client: {ctx.voice_client}")
    if ctx.voice_client:
        print(f"Connected to: {ctx.voice_client.channel}")
        print(f"Is connected: {ctx.voice_client.is_connected()}")
        print(f"Is playing: {ctx.voice_client.is_playing()}")

    # Check all voice clients
    voice_clients = global_bot.voice_clients
    print(f"Total voice clients: {len(voice_clients)}")
    for vc in voice_clients:
        print(f"  - {vc.guild.name}: {vc.channel}")


# Add this to detect multiple bot instances
@global_bot.event
async def on_ready():
    print(f"Bot logged in as {global_bot.user}")
    print(f"Bot ID: {global_bot.user.id}")
    print(f"Connected to {len(global_bot.guilds)} guilds")

    # Check if bot is already in voice channels (might indicate multiple instances)
    if global_bot.voice_clients:
        print("WARNING: Bot already connected to voice channels on startup!")
        for vc in global_bot.voice_clients:
            print(f"  - Already in: {vc.guild.name} -> {vc.channel}")

@global_bot.event
async def on_guild_join(guild):
    guild_id = guild.id
    sv.add_server(guild_id)


@global_bot.event
async def on_member_join(member: discord.Member):

    guild_id = member.guild.id

    sender_server = cast(sv.Server, sv.get_server(guild_id))
    if not sender_server:
        return

    server_config = sender_server.get_config()
    default_role = server_config.get("default_role")
    if default_role is None or default_role == -1:
        print(f"No default role set for guild {member.guild.name}")
        return


    role = member.guild.get_role(default_role)
    if role is None:
        print(f"Role ID {default_role} not found in guild {member.guild.name}")
        return

    try:
        await member.add_roles(role)
    except Exception as e:
        print(f"Failed to assign role: {e}")


@global_bot.command()
@cb.custom_command("administrator")
async def setserverip(ctx, server_ip: str):
    """
    Sets the server IP
    """
    sender_server = cast(sv.Server, ctx.server)

    if not sender_server:
        await ctx.send("Your server does not exist! run !reloadserver to fix")
        return
    sender_server.set_mcserver_ip(server_ip)
    await ctx.send(f"Server ip set")

@global_bot.command()
@cb.custom_command("administrator")
async def setrconport(ctx, port: int):
    """
    Sets the RCON port
    """
    sender_server = cast(sv.Server, ctx.server)

    if not sender_server:
        await ctx.send("Your server does not exist! run !reloadserver to fix")
        return
    sender_server.set_rcon_port(port)

@global_bot.command()
@cb.custom_command("administrator")
async def setrconpassword(ctx, password: str):
    """
    Sets the RCON password
    """

    await ctx.message.delete()

    sender_server = cast(sv.Server, ctx.server)

    if not sender_server:
        await ctx.send("Your server does not exist! run !reloadserver to fix")
        return
    sender_server.set_rcon_password(password)

    await ctx.send("RCON password set")

@global_bot.command()
@cb.custom_command("administrator")
async def setdefaultrole(ctx, role: discord.Role):
    """
    Sets the default role for new members
    """
    sender_server = cast(sv.Server, ctx.server)

    if not sender_server:
        await ctx.send("Your server does not exist! run !reloadserver to fix")
        return

    if not role:
        await ctx.send("Invalid role specified.")
        return

    sender_server.set_default_role(role.id)
    await ctx.send(f"### Default role set to {role.name} ({role.id})")

@global_bot.command()
async def reloadserver(ctx):
    """
    Reloads the server
    """

    print("Generating server files")

    guild_id = ctx.guild.id
    print(f"Guild ID: {guild_id}")
    sv.add_server(guild_id)

@global_bot.command()
async def sendmessage(ctx, *, arg):
    """
    Sends a message to the server
    """
    sender = ctx.author.name

    # Build the JSON structure as Python list/dict
    tellraw_obj = [
        {"text": "[", "color": "white"},
        {"text": sender + " @ Discord", "color": "aqua"},
        {"text": "] ", "color": "white"},
        {"text": arg}
    ]

    #Convert to JSON string (compact)
    tellraw_json = json.dumps(tellraw_obj)

    await brcon.call_mc_command(ctx, f'/tellraw @a {tellraw_json}')

@global_bot.command()
@cb.custom_command("administrator")
async def mccommand(ctx, *, command):
    """
    Sends a command to the Minecraft server via RCON.
    """
    response = await brcon.call_mc_command(ctx, str(command))
    if response:
        await ctx.send(f"### Executed command: {response}")
    else:
        return


@global_bot.command()
async def listplayers(ctx):
    """
    Lists all currently online players
    """
    output = await brcon.call_mc_command(ctx, f"/list")

    if not output:
        return

    players = []

    match = re.search(r'online:\s(.+)', output)
    if match:
        players = [p.strip() for p in match.group(1).split(',')]

    if not players:
        await ctx.send("There are no players currently online.")
        return
    await ctx.send(f"## Players currently online:\n>>> " + '\n'.join(players))


@global_bot.command()
@cb.custom_command("play_sound")
async def play(ctx, *, filename: str):
    await ctx.message.delete()

    sender_server = cast(sv.Server, ctx.server)
    await ctx.send(f"### Queuing: `{filename}`")


    #Get or create music player for this guild
    guild_id = ctx.guild.id
    if guild_id not in vi.music_players:
        vi.music_players[guild_id] = vi.MusicPlayer(ctx)

    player = vi.music_players[guild_id]

    #Download the song
    song_path = await player.get_song_from_soundcloud(filename)
    if not song_path:
        await ctx.send("### Error: Could not download song.")
        return

    player.add_song(song_path)

    # Connect to voice if needed
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        joined = await vi.join_user_channel(ctx)
        if not joined:
            return

    #Start playing if not already playing
    if not player.is_playing:
        print("Starting queue")
        await player.start_queue()


@global_bot.command()
async def skip(ctx):
    """Skip current song"""
    guild_id = ctx.guild.id
    if guild_id not in vi.music_players:
        await ctx.send("### No music player active!")
        return

    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("### Nothing is playing!")
        return


    await ctx.send("### ⏭️ Skipped")
    ctx.voice_client.stop()  # This triggers the after_playing callback


@global_bot.command()
async def stop(ctx):
    """Stop music and clear queue"""
    guild_id = ctx.guild.id

    if guild_id not in vi.music_players:

        await ctx.send("### No music player active!")

    music_player = vi.music_players.get(guild_id)

    for song_file in music_player.queue:
        music_player.remove_song(song_file)

    music_player.stop()
    del music_player

    if ctx.voice_client:
        await ctx.voice_client.disconnect()

    await ctx.send("### Stopping player")


@global_bot.event
async def on_voice_state_update(member, before, after):
    # Clean up if bot gets disconnected
    if member == global_bot.user and before.channel and not after.channel:
        guild_id = before.channel.guild.id
        if guild_id in vi.music_players:
            vi.music_players[guild_id].stop()
            del vi.music_players[guild_id]

#Run bot

bot.run_bot()