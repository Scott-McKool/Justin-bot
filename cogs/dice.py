import asyncio
import discord
from discord.ext import commands
import random

class Dice(commands.Cog):
    def __init__(self, client):
        self.bot = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Dice Cog is ready")

    @commands.command()
    async def flip(self, ctx):
        await ctx.send("Flipping a coin. . .")
        await asyncio.sleep(1)
        if(round(random.random()) == 1):
            return await ctx.send("It's `heads`")
        else:
            return await ctx.send("It's `tails`")

    @commands.command(aliases=["r"])
    async def roll(self, ctx, diceStr):
        if not "d" in diceStr:
            return await ctx.send("must send dice rolls in the format \"[dice ammount]d[dice type]\" ex: 1d6, 2d20 etc. . .")
        numDice, diceType = diceStr.split("d",1)
        try:
            numDice = int(numDice)
            diceType = int(diceType)
        except:
            return await ctx.send("must send dice rolls in the format \"[dice ammount]d[dice type]\" ex: 1d6, 2d20 etc. . .")
        diceSum = 0
        diceResults = ""
        for i in range(numDice):
            roll = round(random.random()*(diceType-1))+1
            diceSum = diceSum + roll
            if roll == 1 or roll == diceType:
                diceResults = diceResults+"**"+str(roll)+"** "
            else:
                diceResults = diceResults+str(roll)+" "
        return await ctx.send(f"{diceStr} = {diceSum}\n{diceResults}")

def setup(client):
    client.add_cog(Dice(client))