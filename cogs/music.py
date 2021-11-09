import discord
import asyncio
from discord.ext import commands, tasks
from discord.ext.commands.errors import BotMissingAnyRole
import datetime
import random
import pafy
import youtube_dl

class Music(commands.Cog):

    def __init__(self, client):
        self.bot = client
        self.mutedPlayers = {}
        self.players = {}
        self.song_queue = {}
        self.songPlaying = False

    def setup(self):
        self.friday.start()
        self.unMute.start()
        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.setup()
        print("Music Cog is ready")

    async def check_queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) > 0:
            await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
            self.song_queue[ctx.guild.id].pop(0)
        else:
            self.songPlaying = False


    async def search_song(self, amount, song, get_url=False):
        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({"format" : "bestaudio", "quiet" : True}).extract_info(f"ytsearch{amount}:{song}", download=False, ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info

    async def play_song(self, ctx, song):
        bestAudio = pafy.new(song).getbestaudio()
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(bestAudio.url)), after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5
        await ctx.send(f"Now playing: `{bestAudio.title}`")

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("You're not in a voice channel.")

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()

        await ctx.author.voice.channel.connect()

    @commands.command()
    async def leave(self, ctx):
        if(self.songPlaying):
            return await ctx.send("i'm playing music right now, shut up")
            
        if ctx.voice_client is not None:
            return await ctx.voice_client.disconnect()

        await ctx.send("Not in a channel, dumbass.")

    @commands.command()
    async def shutup(self, ctx, member : discord.Member):
        userID = member.id
        if userID == None:
            await ctx.send("you gotta give a person to shutup")
            return
        poll = discord.Embed(title=ctx.message.author.name+" wants to shut up"+member.name+" for 30 minutes", description=member.name+" will not be able to play sounds for 30 minutes", colour=discord.Colour.blue())
        poll.add_field(name="Mute", value=":white_check_mark:")
        poll.add_field(name="Don't Mute", value=":no_entry_sign:")
        poll.set_footer(text="Voting ends in 15 seconds.")

        poll_msg = await ctx.send(embed=poll) # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") # yes
        await poll_msg.add_reaction(u"\U0001F6AB") # no
        
        await asyncio.sleep(15) # 15 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)
        
        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.50: # 50% or higher
                skip = True
                self.mutedPlayers[userID] = 30 # number of minutes to mute
                embed = discord.Embed(title="Mute Successful", description="***"+member.name+" can't play songs for 30 minutes***", colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Mute Failed", description="*Voting to shutup someone has failed.*\n\n**vote requires at least 51% of the members to affirm.**", colour=discord.Colour.red())

        embed.set_footer(text="Voting has ended.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

    @tasks.loop(minutes=1)
    async def unMute(self):
        for user in self.mutedPlayers:
            if(self.mutedPlayers[user] > 0):
                self.mutedPlayers[user] = self.mutedPlayers[user] - 1

    @commands.command(aliases=["Play"])
    async def play(self, ctx, *, song=None):
        if(ctx.author.id in self.mutedPlayers):
            if(self.mutedPlayers[ctx.author.id] > 0):
                return await ctx.send("fuck you, you're muted for another "+str(self.mutedPlayers[ctx.author.id])+" minutes, send me a postcard from blocksville")

        if song is None:
            return await ctx.send("You gotta list a song. . .")

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        if("hour" in song):
            await ctx.send("fuck you. no")
            return

        if("chungus" in song):
            await ctx.send("fuck you. no")
            return

        if("among" in song):
            await ctx.send("fuck you. no")
            return

        # handle song where song isn't url
        if not ("http" in song):
            await ctx.send("Searching for song. . .")

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Thats not a real thing.")

            song = result[0]
        songName = pafy.new(song).title

        if self.songPlaying:
            queue_len = len(self.song_queue[ctx.guild.id])

            self.song_queue[ctx.guild.id].append(song)
            return await ctx.send(f"Added song to queue: ({queue_len+1}) `{songName}`.")
        self.songPlaying = True
        await self.play_song(ctx, song)

    @commands.command()
    async def queue(self, ctx): # display the current guilds queue
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("There are currently no songs in the queue.")

        embed = discord.Embed(title="Song Queue", description="", colour=discord.Colour.dark_gold())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            embed.description += f"{i}) {url}\n"

            i += 1

        embed.set_footer(text="List of queued songs")
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not playing any song.")

        if ctx.author.voice is None:
            return await ctx.send("You are not connected to any voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("No")

        poll = discord.Embed(title=f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}", description="**51% of the voice channel must vote to skip for it to pass.**", colour=discord.Colour.blue())
        poll.add_field(name="Skip", value=":white_check_mark:")
        poll.add_field(name="Stay", value=":no_entry_sign:")
        poll.set_footer(text="Voting ends in 15 seconds.")

        poll_msg = await ctx.send(embed=poll) # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") # yes
        await poll_msg.add_reaction(u"\U0001F6AB") # no
        
        await asyncio.sleep(15) # 15 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)
        
        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.50: # 50% or higher
                skip = True
                embed = discord.Embed(title="Skip Successful", description="***Voting to skip the current song was succesful, skipping now.***", colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Skip Failed", description="*Voting to skip the current song has failed.*\n\n**Voting failed, the vote requires at least 51% of the members to skip.**", colour=discord.Colour.red())

        embed.set_footer(text="Voting has ended.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()


    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_paused():
            return await ctx.send("I am already paused.")

        ctx.voice_client.pause()
        await ctx.send("Paused.")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not connected to a voice channel.")

        if not ctx.voice_client.is_paused():
            return await ctx.send("I am already playing a song.")
        
        ctx.voice_client.resume()
        await ctx.send("The current song has been resumed.")

    async def endFriday(self,voiceClient):
        self.songPlaying = False
        await voiceClient.disconnect()

    @tasks.loop(hours=1)
    async def friday(self):
        if self.songPlaying:
            return
        weekday = datetime.datetime.today().weekday()+1
        #if it's friday
        if( weekday == 5 ):
            randomCheck = random.random()*100
            shouldFriday = randomCheck <= 33
            if(shouldFriday):
                # check to see if 3+ people are in a call
                for guild in self.bot.guilds:
                    # if there are no songs currently playing in this server
                    if(len(self.song_queue[guild.id]) == 0):
                        for channel in guild.voice_channels:
                            if(len(channel.members) > 2):
                                try:
                                    VCClient = await channel.connect()
                                    self.FridayPlaying = True

                                    VCClient.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("https://ia801700.us.archive.org/20/items/RebeccaBlackFriday/Rebecca%20Black%20%20-%20Friday.mp3")), after=lambda error:self.bot.loop.create_task(self.endFriday(VCClient)))
                                except Exception as e:
                                    return
                        


def setup(client):
    client.add_cog(Music(client))
