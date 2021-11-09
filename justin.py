import discord
from discord.ext import commands, tasks
import datetime
from cogs.coins import Coins as coins
import os

PREFIX = "!"

TOKEN = "NjYzMjE0MTA5NzI2MDgxMDM2.XhFYgA.daGyAeZKQEK7k2i1JzBZ5ey-5ko"

coolIntents = discord.Intents.default()
coolIntents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=coolIntents)

@bot.event
async def on_ready():
    change_status.start()
    print("bot ready")

@bot.command()
async def ping(ctx):
    await ctx.send(f"pong {round(bot.latency*1000)}ms")

@bot.command()
async def poll(ctx):
    msg = ctx.message.content[5:]
    poll = discord.Embed(title="Poll", description=msg, colour=discord.Colour.blue())
    poll.add_field(name="Agree", value=":white_check_mark:")
    poll.add_field(name="Disagree", value=":no_entry_sign:")
    poll.set_footer(text="Poll initiated by "+ctx.message.author.name)

    poll_msg = await ctx.send(embed=poll)

    await poll_msg.add_reaction(u"\u2705") # yes
    await poll_msg.add_reaction(u"\U0001F6AB") # no

@tasks.loop(seconds=10)
async def change_status():
    date = datetime.datetime(2021, 12, 9, 10)
    event = "till fall semester ends"
    rawTimeString = str(date - datetime.datetime.now())
    if rawTimeString.__contains__(","):
        days , timeTillSchool = rawTimeString.split(",")
    else:
        days = ""
        timeTillSchool = rawTimeString
    hours, minutes = timeTillSchool.split(":")[:-1]
    minutes = str(int(minutes)+1)
    string = days[:-5]+"d:"+hours[1:]+"h:"+minutes+"m " + event
    await bot.change_presence(activity=discord.Game(string))


for filename in os.listdir("./cogs"):
    if(filename.endswith(".py")):
        bot.load_extension(f"cogs.{filename[:-3]}")

bot.run(TOKEN)

