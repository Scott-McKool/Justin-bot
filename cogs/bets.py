from time import time
from asyncio import sleep
import discord
from discord.ext import commands, tasks
import datetime
import os
import json

class bet():
    def __init__(self, id : int, authorID : int, messageID : int, channelID : int, month : int, day : int, year : int, terms : str):
        self.id = id
        self.authorID = authorID
        self.messageID = messageID
        self.channelID = channelID
        self.date = (month, day, year)
        self.terms = terms

    def __repr__(self):
        return f"Event #{self.id} which expires on {self.date} and has the terms: {self.terms}"

    async def sendReminder(self, client):
        # find the message based on its ID
        # get the channel
        channel = await client.fetch_channel(self.channelID)
        # use the channel to get the message
        message = await channel.fetch_message(self.messageID)
        # string to send to chat
        messageString = ""
        # the users that should be notifies, start at [1:] to skip justinbot (who is always the first reaction)
        users = await message.reactions[0].users().flatten()
        # get the author from their ID
        author = await client.fetch_user(self.authorID)
        # add author to the list ov people to mention
        users.append(author)
        users = list(dict.fromkeys(users))
        for user in users[1:]:
            messageString += user.mention + " "
        messageString += "\n"
        messageString += f"```\nthis is a reminder about the bet #{self.id} made by {author}:\n{self.terms}\n```"
        # get context to send message
        ctx = await client.get_context(message)
        await ctx.send(messageString)


class Bets(commands.Cog):
    
    def __init__(self, client):
        self.client = client
        try: 
            os.mkdir("bets/")
        except:
            pass
        

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bets Cog is ready")
        self.loadbets.start()

    async def activateBet(self, filePath):
        # open the file, 
        f = open(f"bets/{filePath}")
        # json decode its contents
        dictBet = json.load(f)
        # turn into a bet object and run the send reminder method
        joebet = bet( dictBet["id"], dictBet["authorID"], dictBet["messageID"], dictBet["channelID"], dictBet["date"][0], dictBet["date"][1], dictBet["date"][2], dictBet["terms"])
        await joebet.sendReminder(self.client)
        # close and delete the file
        f.close()
        os.remove(f"bets/{filePath}")

    @tasks.loop(hours=10)
    async def loadbets(self):
        files = os.listdir("bets/")
        for file in files:
            year, month, day, _id = file.split(",")
            date = datetime.datetime( int(year), int(month), int(day ) )
            # if the date has passed
            if date < datetime.datetime.now():
                await self.activateBet(file)

    @commands.command(aliases=["bets"])
    async def listbets(self, ctx):
        result = ""
        files = os.listdir("bets/")
        for file in files:
            # open the file, 
            f = open(f"bets/{file}")
            # json decode its contents
            dictBet = json.load(f)
            # turn into a bet object and run the send reminder method
            joebet = bet( dictBet["id"], dictBet["authorID"], dictBet["messageID"], dictBet["channelID"], dictBet["date"][0], dictBet["date"][1], dictBet["date"][2], dictBet["terms"])
            # close and delete the file
            f.close()
            result += "```" + str(joebet) + "```"
        await ctx.send(result )

    @commands.command()
    async def bet(self, ctx, month, day, year, *, terms : str = None):
        # the id for this bet
        id = int(time()*10000)
        # when should the bet expire
        try:
            eventDate = datetime.datetime(int(year), int(month), int(day))
        except :
            pass
            return await ctx.send("Error when parsing the date. use the command in this format:\n`!bet <month> <day> <year> <message that represents a bet>`")
        # make sure the date is in the future
        if eventDate < datetime.datetime.now():
            eventDateString = eventDate.strftime("%B %d %Y")
            return await ctx.send(f"The date {eventDateString} is invalid because it is in the past")
        # give a conformation message
        string = f"```Bet made by {ctx.author}\n#{id}\nExpires on {eventDate.strftime('%B %d %Y')}\n{terms}```\nReact with the checkmark to be notified when the bet expires"
        # save a reverence to the message to later retreive the reacions and such
        message = await ctx.send(string)
        await message.add_reaction(u"\u2705")
        # save this bet to the dictionary
        curbet = bet(id, ctx.author.id, message.id, message.channel.id , eventDate.month, eventDate.day, eventDate.year, terms)

        # save the bet to a file
        file = open(f"bets/{year},{month},{day},{id}.json", "w")
        file.write(json.dumps(curbet, default=vars, indent=4))
        file.close()

        

def setup(client):
    client.add_cog(Bets(client))