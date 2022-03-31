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

    async def getAuthor(self, client):
        return await client.fetch_user(self.authorID)

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
        author = self.getAuthor(client)
        # add author to the list ov people to mention
        users.append(author)
        users = list(dict.fromkeys(users))
        for user in users[1:]:
            messageString += user.mention + " "
        messageString += "\n"
        messageString += f"```\nthis is a reminder about the bet #{self.id} made by {author}:\n\n{self.terms}\n```"
        # get context to send message
        ctx = await client.get_context(message)
        await ctx.send(messageString)


class Bets(commands.Cog):
    
    def __init__(self, client):
        self.client = client
        self.betsDir = "bets/"
        try: 
            os.mkdir(f"{self.betsDir}")
        except:
            pass
        

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bets Cog is ready")
        self.loadbets.start()

    def loadBetFile(self, id):
        '''
        loads a bet file to a bet object by id\n
        returns the bet object, or None if no file with the given ID was found
        '''
        id = str(id)
        # loop through the bet files
        for filename in os.listdir(f"{self.betsDir}"):
            # look for the bet by ID
            if id in filename:
                # open and decode the file
                with open(f"{self.betsDir}{filename}") as file:
                    betdict = json.load(file)
                    tempBet = bet( betdict["id"], betdict["authorID"], betdict["messageID"], betdict["channelID"], betdict["date"][0], betdict["date"][1], betdict["date"][2], betdict["terms"])
                    return tempBet
        # return None if no bet file was found
        return None
    

    def deleteBetFile(self, id):
        '''
        deletes a bet file by its ID\n
        returnes true or false for if the file was or was not deleted
        '''
        id = str(id)
        for file in os.listdir(f"{self.betsDir}"):
            if id in file:
                os.remove(f"{self.betsDir}{file}")
                return True
        return False

    async def activateBet(self, id):
        '''
        load in a bet file, send a reminder, then deletes the bet file
        '''
        # load bet
        tempBet = self.loadBetFile(id)
        # send reminder
        await tempBet.sendReminder(self.client)
        # delete file
        self.deleteBetFile(id)


    @tasks.loop(seconds=10)
    async def loadbets(self):
        '''
        loop to ocasionally run and activate any expired bets
        '''
        # loop through all the bets
        for file in os.listdir(f"{self.betsDir}"):
            # parse the file's title
            year, month, day, id = file.split(",")
            date = datetime.datetime( int(year), int(month), int(day ) )
            # if the date has passed
            if date < datetime.datetime.now():
                # activate the bet
                await self.activateBet(id)

    @commands.command()
    async def deletebet(self, ctx, betid):
        '''
        !deletebet <id> -- deletes a bet given its ID
        '''
        tempBet = self.loadBetFile(betid)
        if ctx.author != tempBet.getAuthor():
            return await ctx.send("Only the bet's author can delete this bet reminder")
        if self.deleteBetFile(betid):
            return await ctx.send(f"deleted bet #{betid}")
        return await ctx.send(f"could not find a bet file with the id #{betid}")
                

    @commands.command(aliases=["bets"])
    async def listbets(self, ctx):
        result = ""
        # loop through all the bet files
        for file in os.listdir(f"{self.betsDir}"):
            # get the bet's ID
            _year,_month,_day, id = file.split(",")
            # load the bet file to an object
            tempBet = self.loadBetFile(id)
            # append the bet object's __repr__ to the list
            result += "```" + str(tempBet) + "```"
        # if the list was empty
        if result == "":
            return  await ctx.send("there are no active bets")
        # send the lists
        return await ctx.send(result )

    @commands.command()
    async def bet(self, ctx, month, day, year, *, terms : str = None):
        # the id for this bet
        id = int(time()*10000)
        # when should the bet expire
        # put in a try-catch so that if any of the date conversion goes wrong the user can be notified
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
        string = f"```Bet made by {ctx.author}\n#{id}\nExpires on {eventDate.strftime('%B %d %Y')}\n\n{terms}```\nReact with the checkmark to be notified when the bet expires"
        # save a reverence to the message to later retreive the reacions and such
        message = await ctx.send(string)
        await message.add_reaction(u"\u2705")
        # save this bet to the dictionary
        curbet = bet(id, ctx.author.id, message.id, message.channel.id , eventDate.month, eventDate.day, eventDate.year, terms)

        # save the bet to a file
        file = open(f"{self.betsDir}{year},{month},{day},{id}.json", "w")
        file.write(json.dumps(curbet, default=vars, indent=4))
        file.close()

        

def setup(client):
    client.add_cog(Bets(client))