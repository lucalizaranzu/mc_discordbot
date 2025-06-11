import discord
from discord.ext import commands
import asyncio
import os
import platform

import util

os_name = platform.system()

async def join_user_channel(ctx):
    # Check if the user is in a voice channel
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel

        # Prevent reconnecting if already connected to the correct channel
        if ctx.voice_client and ctx.voice_client.is_connected():
            if ctx.voice_client.channel == channel:
                print("Already connected to the user's voice channel.")
                return True
            else:
                await ctx.voice_client.disconnect()
                print("Disconnected from old channel.")

        try:
            await channel.connect()
            print(f"Connected to channel: {channel}")
            return True
        except Exception as e:
            print(f"Error connecting to voice channel: {e}")
            await ctx.send("Failed to connect to your voice channel.")
            return False
    else:
        await ctx.send("### You're not in a voice channel!")
        print("ctx.author.voice is None")
        return False

async def leave_voice_channel(ctx):

    if ctx.voice_client and ctx.voice_client.is_connected():
        await ctx.voice_client.disconnect()
        print(f"Disconnected from voice channel: {ctx.voice_client.channel.name}")

        await ctx.send("Disconnected from the voice channel.")
    else:
        print("Bot is not connected to any voice channel.")
        await ctx.send("### I'm not connected to any voice channel!")

async def stop_playing_sound(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        print("Stopped playing sound.")
    else:
        print("No sound is currently playing.")
        await ctx.send("### No sound is currently playing.")

async def play_sound_in_channel(config, ctx, sound_file: str):

    await join_user_channel(ctx)

    #Validate sound file
    if not os.path.exists(sound_file):
        print(f"ERROR: Sound file '{sound_file}' does not exist.")
        await ctx.send(f"### Error: Sound file not found.")
        return

    #Get and validate FFmpeg path
    ffmpeg_path = util.get_program_path(config, os_name, "ffmpeg")
    if not ffmpeg_path:
        print("ERROR: Could not resolve FFmpeg path from config.")
        return

    if not util.check_program_path(ffmpeg_path):
        return

    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.stop()

    try:
        audio_source = discord.FFmpegPCMAudio(executable=ffmpeg_path, source=sound_file)
        voice_client.play(audio_source)
        await ctx.send(f"Now playing `{os.path.basename(sound_file)}` in `{voice_client.channel.name}`.")
    except Exception as e:
        print(f"ERROR: Failed to play audio: {e}")
        await ctx.send("### Error: Failed to play audio.")