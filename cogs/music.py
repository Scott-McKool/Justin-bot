from discord.ext import commands
from yt_dlp import YoutubeDL
from requests import get
import discord
import time

class Music(commands.Cog):
    def __init__(self, client):
        self.bot = client
        # video queue
        # a dict where keys are server IDs and values are video, tuples (video name, video duration, video audio direct link)
        self.queue = {}
        # blackListed members
        # a dict where keys are server IDs and values are dicts (keys are memberIDs and values are the timecode they are blackListed until)
        self.blackListed = {}
        # track if the bot is currently playing music in each server
        # dict with server IDs as keys and bool as values
        self.isPlaying = {}

    def setup(self):
        print()
        pass

    @commands.Cog.listener()
    async def on_ready(self):
        self.setup()
        print("Music Cog is ready")

    def searchVideo(self, name):
        '''takes in a string name as a video title and returns a tuple of the direct link to the audio and the video title'''
        with YoutubeDL({'format': 'bestaudio', 'noplaylist':'True'}) as ydl:
            try:
                # try and visit the passed name on the web
                # if it is a valid url then this will pass, if it is just some string it will raise an exception
                get(name) 
            except:
                # if an exeption is raised, this is just some string, so search for it on youtube
                videoData = ydl.extract_info(f"ytsearch:{name}", download=False)['entries'][0]
            else:
                # if no exception was raised, this is a url, use yt-dlp to treat it like a youtube url
                videoData = ydl.extract_info(name, download=False)
        # extract useful data from the video data
        url = videoData.get("url", None)
        title = videoData.get("title", None)
        duration = videoData.get("duration", None)

        return url, title, duration
    
    def isBlackListed(self, serverID:int, memberID:int):
        '''Takes in a player id and returns the ammount of time in seconds a member is blackListed from pllaying youtube videos for.
        if they are not blackListed, returns false'''
        # the list of potentially blacklisted members in the given server
        blackListedMembers = self.blackListed.get(serverID, {})
        # the timecode for when the given member will no longer be blacklisted
        blackListedUntil = blackListedMembers.get(memberID, 0)
        # is the player currently blacklisted
        timeRemaining = blackListedUntil - time.time()
        if timeRemaining < 0:
            return False
        return round(timeRemaining)

    async def checkQueue(self, ctx):
        serverID = ctx.guild.id
        queue = self.queue.get(serverID, [])
        # if there are no more songs to play
        if len(queue) == 0:
            self.isPlaying[serverID] = False
            return
        # play the next song in the queue
        title, _duration, url = queue[0]
        # remove the video from the queue
        self.queue.setdefault(serverID, []).pop(0)
        await self.playAudio(ctx, url, title)

    async def playAudio(self, ctx, url, title):
        # marks this server as now playing a video
        self.isPlaying[ctx.guild.id] = True
        # before options to that the ffmpeg stret will try to reconnect if interupted
        beforeOptions = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}
        # play the audio from the source URL
        ctx.voice_client.play(discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(url,
                                    before_options=beforeOptions)),
                                    after=lambda error: self.bot.loop.create_task(self.checkQueue(ctx)))
        ctx.voice_client.source.volume = 0.2
        # send notification
        await ctx.send(f"Now playing: `{title}`")

    @commands.command(aliases=["Play"])
    async def play(self, ctx, *, title=None):
        serverID = ctx.guild.id

        blackListed = self.isBlackListed(serverID, ctx.author.id)
        if blackListed:
            return await ctx.send(f"You cannot play videos, you are blacklisted for another {blackListed//60} minutes.")

        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel")

        if not title:
            return await ctx.send("You must give a video title.")
        
        # if the bot is not in a voice channel, join the author's
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        # if the bot is in a call, but a different one than the author
        elif ctx.voice_client.channel.id != ctx.author.voice.channel.id:
            # if the bot is playing a video in this server already
            if self.isPlaying.get(serverID, False):
                # don't switch channels
                return await ctx.send("You must be in the same channel as the bot to add videos to the queue.")
            else:
                # disconnect from current channel
                await ctx.voice_client.disconnect()
                # connect to author's channel
                await ctx.author.voice.channel.connect()

        await ctx.send(f"Searching for \"{title}\". . .")

        # search up the 
        url, video_title, duration = self.searchVideo(title)

        # if the bot is playing a video in this server already
        if self.isPlaying.get(serverID, False):

            self.queue.setdefault(serverID, []).append((video_title, duration, url))
            return await ctx.send(f"added \"{video_title}\" `{duration//60}:{duration%60}` to the queue")
        
        # if the bot is not playing a video
        await self.playAudio(ctx, url, video_title)

    @commands.command(aliases=["joemama"])
    async def blacklist(self, ctx, member:discord.Member):
        serverID = ctx.guild.id
        userID = member.id
        if userID == None:
            await ctx.send("you gotta give a person to shutup")
            return
        
        poll = discord.Embed(title=ctx.message.author.name+" wants to black list"+member.name+" for 30 minutes", description=member.name+" will not be able to play videos for 30 minutes\n\nmore than half of the voice call must vote for this to pass.", colour=discord.Colour.blue())
        poll.add_field(name="To vote in favor of blackisting", value=":white_check_mark:")
        poll.set_footer(text="Voting ends in 10 seconds.")

        poll_msg = await ctx.send(embed=poll) # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") # yes
        
        time.sleep(10) # 10 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)
        
        # count up the number of people in the VC that voted
        votes = 0
        for reaction in poll_msg.reactions:
            if reaction.emoji == u"\u2705":
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and not user.bot:
                        votes += 1

        # the number of people in the same channel as the bot (minus 1 to account for the bot)
        numMembers = len(ctx.voice_client.channel.members) - 1
        # if more then half the members voted yes
        if votes/numMembers > 0.5:
            embed = discord.Embed(title="Vote Successful", description=f"***Voting to black list \"{member.name}\" was succesful, they cannot play videos for 30 minutes.***", colour=discord.Colour.green())
            # set the timecode for when the user should be un-blackListed to 30 minutes in the future
            self.blackListed.setdefault(serverID, {}).setdefault(member.id, time.time() + (3 * 60))
            embed.set_footer(text="Voting has ended.")
            return await poll_msg.edit(embed=embed)
        
        # if half or less of the VC voted yes
        embed = discord.Embed(title="Vote Failed", description=f"*Voting to black list \"{member.name}\"has failed.*\n\n**Voting failed, the vote requires at least 51% of the members to vote yes.**", colour=discord.Colour.red())
        embed.set_footer(text="Voting has ended.")
        return await poll_msg.edit(embed=embed)


def setup(client):
    client.add_cog(Music(client))