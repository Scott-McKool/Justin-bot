import discord
from discord.ext import commands, tasks
import datetime
import os
import urllib.request
import time

PREFIX = "!"

TOKEN = "NjYzMjE0MTA5NzI2MDgxMDM2.XhFQRQ.5uhTIzQp_MRrTauge8DQ2vu9uE8"

coolIntents = discord.Intents.default()
coolIntents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=coolIntents)

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

@tasks.loop(seconds=10)
async def change_status():
    date = datetime(2021, 12, 10, 0, 0)
    event = "till fall semester ends"
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


for filename in os.listdir("/home/pi/Justin-bot/cogs"):
    if(filename.endswith(".py")):
        bot.load_extension(f"cogs.{filename[:-3]}")

# wait till an internet connection is established before trying to login
while(True):
    try:
        # will throw an error if not on internet
        urllib.request.urlopen("http://google.com")
    except Exception as e:
        print("did not log in, not connected to internet, retrying in 10 seconds. . .")
        time.sleep(10)
        continue
    bot.run(TOKEN)
    break

