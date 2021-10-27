from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from discord import TextChannel
from youtube_dl import YoutubeDL
import asyncio
from cogs.base_cog import BaseCog

#info about a song
class Song():
    url = ""
    title = ""
    duration = None

    #construct a song
    def __init__(self, _url, _title, _duration=0):
        self.url = _url
        self.title = _title
        self.duration = _duration

#gets the info of a playlist
def get_song_info(song_name):
    #options for youtube dl
    YDL_OPTIONS = {'format': 'bestaudio', 'yesplaylist': 'True', 'quiet' : "True"}

    #search for the video as a link
    songs = []
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(song_name, download=False)

            #if the result is a song, get and return it
            if "url" in info:
                songs.append(Song(info['url'], info["title"], info["duration"]))
                return songs
            #otherwise if the result is a playlist, get all songs and return them
            elif "entries" in info:
                for entry in info["entries"]:
                    songs.append(Song(entry['url'], entry["title"], entry["duration"]))
                return songs
        except:
            #get the search result for the song name
            info = ydl.extract_info(f"ytsearch:{song_name}", download=False)

            #get and return the first search result
            first_result = info["entries"][0]
            songs.append(Song(first_result['url'], first_result["title"], first_result["duration"]))
            return songs

class cog_music(BaseCog):
    def __init__(self, client):
        self.client = client
        self.queues = {}
        self.song_done_future = None

    #plays the next song in the queue
    async def play_songs(self, ctx):
        #ffmpeg options
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        while len(self.queues[str(ctx.message.guild.id)]) != 0:
            #get and remove the next song in the queue
            song = self.queues[str(ctx.message.guild.id)].pop(0)

            #get the voice client of the bot in the guild
            voice = get(self.client.voice_clients, guild=ctx.guild)

            #make a future for the audio player
            loop = asyncio.get_event_loop()
            self.song_done_future = loop.create_future()

            #play the next song in the queue
            print(f"Playing song {song.title}")
            voice.play(FFmpegPCMAudio(song.url, **FFMPEG_OPTIONS), after=lambda _: self.song_done_future.set_result(True))
            await ctx.send(f'Playing song `{song.title}`!')

            #wait for the future to be marked done
            await self.song_done_future
            #destroy the future
            self.song_done_future = None
            await asyncio.sleep(1)
            voice.stop()
        self.queues.remove(str(ctx.message.guild.id))

    @commands.group(pass_context=True, invoke_without_command=True)
    async def music(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("<@521285684271513601> Implement a help message system already you lazy bitch")

    @music.group(pass_context=True, invoke_without_command=True)
    async def queue(self, ctx):
        #does the server have a queue?
        g_id = str(ctx.message.guild.id)
        if not g_id in self.queues:
            await ctx.send("No queue!")
            return
        if self.queues[g_id] == []:
            await ctx.send("No queue!")
            return

        #template string for string.format
        queue_entry_template = "\n\t{0}. {1}: Length: {2}"

        #start the message as a css codeblock(for looks only)
        final_message = "```css\nQueue:"
        #iterate through each song in the queue
        for song_i in range(len(self.queues[g_id])):
            #get the current song
            song = self.queues[str(ctx.message.guild.id)][song_i]
            #add the formatted template string onto the message
            final_message += queue_entry_template.format(
                song_i + 1,
                song.title,
                song.duration
            )
        #end the code block
        final_message += "\n```"

        #send the message
        await ctx.send(final_message)

    # command for bot to join the channel of the user, if the bot has already joined and is in a different channel, it will move to the channel the user is in
    @music.command()
    async def join(self, ctx):
        #get the voice channel of the user
        auth_voice = ctx.message.author.voice
        channel = None
        if auth_voice is None:
            await ctx.send("You aren't in a voice channel!")
        else:
            channel = ctx.message.author.voice.channel
            if channel is None:
                await ctx.send("You aren't in a voice channel!")

        #get our voice client
        voice = get(self.client.voice_clients, guild=ctx.guild)

        #are we already connected to a voice channel
        if voice and voice.is_connected():
            #yes, move to the user's channel
            await voice.move_to(channel)
        else:
            #no, connect to the user's channel
            voice = await channel.connect()

    #play a video, either by searching or by url
    @music.command()
    async def play(self, ctx):
        #make sure we're in the same voice channel as the user
        try:
            await self.join(ctx)
        except:
            return

        #get the voice client of the bot in the guild
        voice = get(self.client.voice_clients, guild=ctx.guild)

        #get the song name(everything after the prefix and command)
        song_name = ctx.message.content[len(ctx.prefix) + len("music play") + 1:]
        print(song_name)

        #does this server have a queue?
        if not str(ctx.message.guild.id) in self.queues:
            #nope, add a queue
            self.queues.append(str(ctx.message.guild.id), [])

        #add all the songs(for one song we still get a playlist of one) to the queue
        song_info = get_song_info(song_name)
        self.queues[str(ctx.message.guild.id)] += song_info

        #only begin playing if we aren't already playing a song
        if not voice.is_playing():
            #we aren't playing a song, start playing the queue
            print(f"\n\t<<<{ctx.message.author.guild.name}::{ctx.message.author.name}#{ctx.message.author.discriminator}>>>\n\t\tPlaying song {song_name}")
            await self.play_songs(ctx)
        else:
            #just stop at queuing the song
            print(f"\n\t{ctx.message.author.guild.name}::{ctx.message.author.name}#{ctx.message.author.discriminator} \n\t\tQueuing song {song_name}")
            #send a message acknowledging the command
            if len(song_info) > 1:
                await ctx.send(f"Queueing `{len(song_info)}` songs...")
            else:
                await ctx.send(f"Queueing `{song_info[0].title}`...")

    # command to resume voice if it is paused
    @music.command()
    async def resume(self, ctx):
        #get the client voice
        voice = get(self.client.voice_clients, guild=ctx.guild)

        #only resume if the voice isn't playing
        if not voice.is_playing():
            #resume
            voice.resume()
            await ctx.send('Resuming! :arrow_forward:')
        else:
            await ctx.send("Already Playing!")


    # command to pause voice if it is playing
    @music.command()
    async def pause(self, ctx):
        #get the voice client
        voice = get(self.client.voice_clients, guild=ctx.guild)

        #only pause if the voice is playing
        if voice.is_playing():
            #pause
            voice.pause()
            await ctx.send('Paused! :pause_button:')
        else:
            await ctx.send("Already Paused!")


    # command to stop voice
    @music.command()
    async def stop(self, ctx):
        #get the voice client
        voice = get(self.client.voice_clients, guild=ctx.guild)

        #only stop if the voice is playing
        if voice.is_playing():
            #stop
            voice.stop()
            self.queues[str(ctx.message.guild.id)] = []
            await ctx.send('Stopped! :stop_button:')
        else:
            await ctx.send("Already Stopped!")

    @queue.command()
    async def empty(self, ctx):
        self.queues[str(ctx.message.guild.id)] = []
        await ctx.send("Queue emptied! :boom:")

    @music.command()
    async def skip(self, ctx):
        self.song_done_future.set_result(True)
        await ctx.send("Song skipped! :track_next:")

    @music.command()
    async def remove(self, ctx, index):
        #try to get the index as an integer
        int_index = None
        try:
            int_index = int(index)
        except ValueError:
            await ctx.send(f"Can't remove song `{index}`! Index not a number!")
            return

        #try to remove the index
        try:
            self.queues[str(ctx.message.guild.id)].pop(int_index)
        except IndexError:
            await ctx.send(f"Can't remove song `{int_index}`! Not in queue!")
            return

        #success!
        await ctx.send(f"Removed song `{int_index}`! :boom:")
