#!/usr/bin/python3
from discord.ext import commands, tasks
import urllib.request
import justinConfig
import datetime
import discord
import asyncio
import time
import os

coolIntents = discord.Intents.all()
coolIntents.members = True

bot = commands.Bot(command_prefix=justinConfig.PREFIX, intents=coolIntents)

@bot.event
async def on_ready():
    change_status.start()
    print("bot ready")

@bot.command()
async def ping(ctx):
    '''
    Gets Justinbot's latency 
    '''
    await ctx.send(f"pong {round(bot.latency*1000)}ms")

@bot.command()
async def poll(ctx):
    '''
    Simple command that makes a poll embed with voting reactions
    '''
    msg = ctx.message.content[5:]
    poll = discord.Embed(title="Poll", description=msg, colour=discord.Colour.blue())
    poll.add_field(name="Yes", value=":white_check_mark:")
    poll.add_field(name="No", value=":no_entry_sign:")
    poll.set_footer(text="Poll initiated by "+ctx.message.author.name)

    poll_msg = await ctx.send(embed=poll)

    await poll_msg.add_reaction(u"\u2705") # yes
    await poll_msg.add_reaction(u"\U0001F6AB") # no

@bot.command()
async def pfp(ctx, member : discord.Member):
    '''
    pastes a given user's discord avitar in chat
    '''
    if(not member):
        return await ctx.send("invalid member")
    return await ctx.send(member.avatar_url)

@tasks.loop(minutes=1)
async def change_status():
    date = datetime.datetime(2022, 8, 22, 0, 0)
    event = "till Fall semester begins"
    rawTimeString = str(date - datetime.datetime.now())
    if rawTimeString.__contains__(","):
        days , timeTillSchool = rawTimeString.split(",")
    else:
        days = "0"
        timeTillSchool = rawTimeString
    hours, minutes = timeTillSchool.split(":")[:-1]
    minutes = str(int(minutes))
    string = (days[:-5].zfill(1))+"d:"+(hours[1:].zfill(2))+"h:"+(minutes.zfill(2))+"m " + event
    await bot.change_presence(activity=discord.Game(string))


for filename in os.listdir(f"{justinConfig.BOT_DIR}cogs"):
    if(filename.endswith(".py")):
        asyncio.run(bot.load_extension(f"cogs.{filename[:-3]}"))

# wait till an internet connection is established before trying to login
while(True):
    try:
        # will throw an error if not on internet
        urllib.request.urlopen("http://google.com")
    except Exception as e:
        print("did not log in, not connected to internet, retrying in 10 seconds. . .")
        time.sleep(10)
        continue
    bot.run(justinConfig.DISCORD_TOKEN)
    break

