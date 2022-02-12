from discord.ext import commands
import requests
from re import findall
import os
import wave
import audioop

class EarRape(commands.Cog):
    
    def __init__(self, client) -> None:
        super().__init__()
        self.bot = client
        # how many rms is considered ear rape
        self.earRapeThreshold = 16000
        # attachment formats that have audio in them
        self.videoAudioFormats = [
            "mp3",
            "mp4",
            "avi",
            "mkv",
            "webm",
            "mov",
            "wav"
            ]

    @commands.Cog.listener()
    async def on_ready(self):
        print("EarRape detection Cog is ready")

    async def analyzeDiscordAttachment(self, link, ctx, message):
        pathToTmp = "/home/pi/Justin-bot/tmp/"
        try: 
            os.mkdir(pathToTmp)
        except:
            pass

        # name of file
        fileName = link.split("/")[-1]

        # download video/audio and put into a file
        content = requests.get(link).content
        with open(f"{pathToTmp}{fileName}", "wb") as file:
            file.write(content)
            pass
        file.close()

        #format the audio to wav format
        fileNameWav = fileName.split(".")[0] + ".wav"
        os.system(f"ffmpeg -i {pathToTmp}{fileName} -vn -acodec pcm_s16le -ac 1 -ar 44100 -f wav {pathToTmp}{fileNameWav}")
        os.remove(f"{pathToTmp}{fileName}")

        # read the audio and determine loudness
        wavContent = wave.open(f"{pathToTmp}{fileNameWav}")
        rms = audioop.rms(wavContent.readframes(wavContent.getnframes()), wavContent.getsampwidth())
        os.remove(f"{pathToTmp}{fileNameWav}")
        if rms > self.earRapeThreshold:
            await message.add_reaction("🔊")
            await message.add_reaction("⚠️") 
        
    async def analyzeYoutubeVideo(self, link, ctx, message):
        ctx.send("joe mama")

    @commands.Cog.listener("on_message")
    async def earRapeCheck(self, message):
        '''
        downloads any embeded video/audio and checks its volume, then marks loud things as loud
        '''
        ctx = await self.bot.get_context(message)
        if len(message.attachments) > 0:
            for attachment in message.attachments:
                # if an attachment is a video or audio
                if attachment.url.split(".")[-1] in self.videoAudioFormats:
                    await self.analyzeDiscordAttachment(attachment.url, ctx, message)
        # get all links in the image
        links = findall("(https?://\S+)", message.content)
        for link in links:
            #discord links
            if "https://cdn.discordapp.com/" in link:
                await self.analyzeDiscordAttachment(link, ctx, message)
            #youtube links
            if "https://www.youtu" in link:
                await self.analyzeYoutubeVideo(link, ctx, message)

                


def setup(client):
    client.add_cog(EarRape(client))