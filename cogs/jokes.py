import discord
from discord.ext import commands
from asyncio import sleep
import requests

class Jokes(commands.Cog):
    
    def __init__(self, client) -> None:
        super().__init__()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Jokes Cog is ready")

    @commands.command()
    async def joke(self, ctx):
        joke = requests.get("https://v2.jokeapi.dev/joke/Miscellaneous,Dark,Pun,Spooky,Christmas?blacklistFlags=nsfw,religious,political,racist,sexist,explicit").json()
        if joke["type"] == "twopart":
            await ctx.send(joke["setup"])
            await sleep(2)
            return await ctx.send(joke["delivery"])
        else:
            return await ctx.send(joke["joke"])

async def setup(client):
    await client.add_cog(Jokes(client))