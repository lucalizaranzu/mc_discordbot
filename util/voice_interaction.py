import discord

import platform
import os
import uuid
import yt_dlp
import threading


from asyncio import sleep, run_coroutine_threadsafe
from bot import global_bot


import asyncio
import time

from . import server as sv
import tempfile
from discord.utils import get

command_execution_tracker = {}

from . import util as ut

os_name = platform.system()

music_players = {} #music player objects

class MusicPlayer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.is_playing = False
        self.queue = []
        self.current_song = None

    def add_song(self, song_path):
        self.queue.append(song_path)

    async def get_song_from_soundcloud(self, sound_file: str):
        ffmpeg_path = ut.get_program_path("FFMPEG")
        if not ffmpeg_path:
            print("ERROR: Could not resolve FFmpeg path from config.")
            await self.ctx.send("### Error: FFmpeg not found in config.")
            return

        if not ut.check_program_path(ffmpeg_path):
            await self.ctx.send("### Error: FFmpeg path is not valid.")
            return

        is_soundcloud_link = "soundcloud.com" in sound_file
        temp_base = f"sc_{uuid.uuid4()}"
        output_path = os.path.join("temp", temp_base)
        query = sound_file if is_soundcloud_link else f"scsearch1:{sound_file}"
        output_file = output_path + ".mp3"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': ffmpeg_path,
            'quiet': True,
        }

        def download_audio():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([query])

        try:
            await asyncio.to_thread(download_audio)
        except Exception as e:
            print(f"### ERROR: Failed to download SoundCloud audio: {e}")
            await self.ctx.send("### Error: Failed to retrieve audio from SoundCloud.")
            return

        return output_file

    async def start_queue(self):
        """Start playing the queue - only call this once"""
        if self.is_playing:
            print("Queue already running")
            return

        self.is_playing = True
        await self.pla_next_song()

    async def pla_next_song(self):
        """Internal method to play the next song"""
        voice_client = self.ctx.voice_client

        # Check if we're still connected
        if not voice_client or not voice_client.is_connected():
            print("Voice client disconnected, stopping queue")
            self.is_playing = False
            return

        # Check if already playing (shouldn't happen but safety check)
        if voice_client.is_playing():
            print("Already playing, waiting...")
            return

        next_song = self.queue.pop(0)
        self.current_song = next_song

        if not os.path.exists(next_song):
            print(f"Song file not found: {next_song}")
            # Try next song
            await self.pla_next_song()
            return

        # Play the song
        await self._play_file(next_song)

    async def _play_file(self, sound_file_path):
        """Play a single file"""
        print("Play file")

        ffmpeg_path = ut.get_program_path("FFMPEG")
        if not ffmpeg_path or not ut.check_program_path(ffmpeg_path):
            await self.ctx.send("### Error: FFmpeg not found.")
            self.is_playing = False
            return

        voice_client = self.ctx.voice_client
        if not voice_client or not voice_client.is_connected():
            print("Voice client not connected")
            self.is_playing = False
            return

        song_name = os.path.basename(sound_file_path)

        def after_playing(error):
            if error:
                print(f"Player error: {error}")
            else:
                print(f"Song finished playing normally: {song_name}")

            def delayed_cleanup():
                try:
                    # Double-check that playback actually stopped
                    if not voice_client.is_playing() and not voice_client.is_paused():
                        self.remove_song(sound_file_path)
                        print(f"Cleaned up: {sound_file_path}")

                        # Clear the current audio source reference
                        self.current_audio_source = None

                        # Continue with next song if queue has items
                        if self.is_playing and len(self.queue) > 0:
                            try:
                                future = run_coroutine_threadsafe(self.pla_next_song(), global_bot.loop)
                            except Exception as ie:
                                print(f"Error scheduling next song: {ie}")
                                self.is_playing = False
                        else:
                            print("Queue empty or player stopped")
                            self.is_playing = False
                    else:
                        print("Audio still playing, cleanup cancelled")

                except Exception as ie:
                    print(f"Cleanup error: {ie}")

            # Longer delay to ensure FFmpeg properly releases the file
            threading.Timer(2.0, delayed_cleanup).start()

        try:
            # Create audio source with better options
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }

            audio_source = discord.FFmpegPCMAudio(
                executable=ffmpeg_path,
                source=sound_file_path,
                **ffmpeg_options
            )

            # Store reference to prevent garbage collection
            self.current_audio_source = audio_source

            voice_client.play(audio_source, after=after_playing)
            print(f"Started playing: {song_name}")

        except Exception as e:
            print(f"Failed to play audio: {e}")
            await self.ctx.send("### Error: Failed to play audio.")
            self.is_playing = False

            # Clean up on failure
            try:
                if os.path.exists(sound_file_path):
                    os.remove(sound_file_path)
            except Exception as cleanup_error:
                print(f"Error cleaning up failed file: {cleanup_error}")

    def remove_song(self, song_path):
        """Remove a song from the queue and delete the file"""

        try:
            if os.path.exists(song_path):
                os.remove(song_path)
                print(f"Removed song file: {song_path}")
        except Exception as e:
            print(f"Error removing song file {song_path}: {e}")

        if song_path in self.queue:
            self.queue.remove(song_path)
        elif song_path == self.current_song:
            self.current_song = None  # or whatever sentinel you use
        else:
            print(f"Song not found in queue: {song_path}")

    import os

    def stop(self):
        """Stop the music player and clean up temp files"""
        self.is_playing = False
        voice_client = self.ctx.voice_client

        if voice_client and voice_client.is_playing():
            voice_client.stop()

        # Clean up all files in the temp directory
        temp_dir = "temp"
        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        print(f"Removed temp file: {file_path}")
                    except Exception as e:
                        print(f"Error removing temp file {file_path}: {e}")
        except FileNotFoundError:
            print("Temp folder not found.")


async def join_user_channel(ctx):
      # Create unique execution ID
    execution_id = f"{time.time()}_{ctx.author.id}"

    # Check if command is already running for this guild
    guild_id = ctx.guild.id
    if guild_id in command_execution_tracker:
        print(f"WARNING: Command already running for guild {guild_id}. Existing: {command_execution_tracker[guild_id]}")
        await ctx.send("Command already running, please wait...")
        return

    # Mark this guild as having a running command
    command_execution_tracker[guild_id] = execution_id

    try:
        if not ctx.author.voice:
            print("User not in voice channel")
            await ctx.send("You're not in a voice channel!")
            return

        channel = ctx.author.voice.channel
        print(f"User in channel: {channel}")
        print(f"Current voice client: {ctx.voice_client}")

        # Add a small delay to prevent rapid-fire connections
        await asyncio.sleep(0.5)

        if ctx.voice_client:
            if ctx.voice_client.channel == channel:
                print("Already in the correct channel")
                await ctx.send("Already connected to your channel!")
            else:
                print(f"Moving from {ctx.voice_client.channel} to {channel}")
                await ctx.voice_client.move_to(channel)
                print("Successfully moved!")
                await ctx.send(f"Moved to {channel.name}")
        else:
            print(f"Connecting to {channel}")
            await channel.connect()
            print("Successfully connected!")
            await ctx.send(f"Connected to {channel.name}")

    except Exception as e:
        print(f"Connection failed: {e}")
        await ctx.send(f"Connection failed: {e}")
        return False
    finally:
        # Always remove from tracker when done
        if guild_id in command_execution_tracker:
            del command_execution_tracker[guild_id]
    return True