from time import time
import discord
from discord.ext import commands, tasks
import datetime
import os
from json import dumps, load
from numpy import sort
import justinConfig

class Event_Reminder():
    def __init__(self, id : int, authorID : int, messageID : int, channelID : int, month : int, day : int, year : int, terms : str):
        self.id = id
        self.authorID = authorID
        self.messageID = messageID
        self.channelID = channelID
        self.date = (month, day, year)
        self.terms = terms

    def __str__(self):
        return f"Event #{self.id} which expires on {self.date} and has the terms: {self.terms}"

    def __repr__(self):
        return self.__str__()

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
        # the users that should be notifies, 
        users = await message.reactions[0].users().flatten()
        # get the author from their ID
        author = await self.getAuthor(client)
        # add author to the list ov people to mention
        users.append(author)
        users = list(dict.fromkeys(users))
        # start at [1:] to skip justinbot (who is always the first reaction)
        for user in users[1:]:
            messageString += user.mention + " "
        messageString += "\n"
        messageString += f"```\nthis is a reminder about the event #{self.id} made by {author}:\n\n{self.terms}\n```"
        # get context to send message
        ctx = await client.get_context(message)
        await ctx.send(messageString)


class Reminder(commands.Cog):
    
    def __init__(self, client):
        self.client = client
        self.eventsDir = f"{justinConfig.BOT_DIR}events/"
        try: 
            os.mkdir(f"{self.eventsDir}")
        except:
            pass
        

    @commands.Cog.listener()
    async def on_ready(self):
        print("Event reminder Cog is ready")
        self.loadEvents.start()

    def loadEventFile(self, id):
        '''
        loads an event file to an event object by id\n
        returns the event object, or None if no file with the given ID was found
        '''
        id = str(id)
        # loop through the event files
        for filename in os.listdir(f"{self.eventsDir}"):
            # look for the event by ID
            if id in filename:
                # open and decode the file
                with open(f"{self.eventsDir}{filename}") as file:
                    eventDict = load(file)
                    tempEvent = Event_Reminder( eventDict["id"], eventDict["authorID"], eventDict["messageID"], eventDict["channelID"], eventDict["date"][0], eventDict["date"][1], eventDict["date"][2], eventDict["terms"])
                    return tempEvent
        # return None if no event file was found
        return None
    

    def deleteEventFile(self, id):
        '''
        deletes a event file by its ID\n
        returnes true or false for if the file was or was not deleted
        '''
        id = str(id)
        for file in os.listdir(f"{self.eventsDir}"):
            if id in file:
                os.remove(f"{self.eventsDir}{file}")
                return True
        return False

    async def activateEvent(self, id):
        '''
        load in a event file, send a reminder, then deletes the event file
        '''
        # load event
        tempEvent = self.loadEventFile(id)
        # send reminder
        await tempEvent.sendReminder(self.client)
        # delete file
        self.deleteEventFile(id)


    @tasks.loop(hours=10)
    async def loadEvents(self):
        '''
        loop to ocasionally run and activate any expired events
        '''
        # loop through all the events
        for file in os.listdir(f"{self.eventsDir}"):
            # parse the file's title
            year, month, day, id = file.split(",")
            date = datetime.datetime( int(year), int(month), int(day ) )
            # if the date has passed
            if date < datetime.datetime.now():
                # activate the event
                await self.activateEvent(id)

    @commands.command(aliases=["deleteevent", "deleteEvent", "removeEvent"])
    async def removeevent(self, ctx, eventid):
        '''
        !deleteevent <id> -- deletes an event given its ID
        '''
        tempEvent = self.loadEventFile(eventid)
        if ctx.author != await tempEvent.getAuthor(self.client):
            return await ctx.send("Only the event's author can delete this event reminder")
        if self.deleteEventFile(eventid):
            return await ctx.send(f"deleted event #{eventid}")
        return await ctx.send(f"could not find a event file with the id #{eventid}")
                

    @commands.command(aliases=["events", "reminders"])
    async def listEvents(self, ctx):
        result = ""
        # loop through all the events files
        for file in sort(os.listdir(f"{self.eventsDir}")):
            # get the event's ID
            _year,_month,_day, id = file.split(",")
            # load the event file to an object
            tempEvent = self.loadEventFile(id)
            # append the event object's __repr__ to the list
            result += "```" + str(tempEvent) + "```"
        # if the list was empty
        if result == "":
            return  await ctx.send("there are no active reminders")
        # send the lists
        return await ctx.send(result )

    @commands.command(aliases=["event", "reminder"])
    async def makeevent(self, ctx, month, day, year, *, terms : str = None):
        # the id for this event
        id = int(time()*10000)
        # when should the event reminder expire
        # put in a try-catch so that if any of the date conversion goes wrong the user can be notified
        try:
            eventDate = datetime.datetime(int(year), int(month), int(day))
        except :
            pass
            return await ctx.send("Error when parsing the date. use the command in this format:\n`!event <month> <day> <year> <message that represents a reminder>`")
        # make sure the date is in the future
        if eventDate < datetime.datetime.now():
            eventDateString = eventDate.strftime("%B %d %Y")
            return await ctx.send(f"The date {eventDateString} is invalid because it is in the past")
        # give a conformation message
        string = f"```Event reminder made by {ctx.author}\n#{id}\nExpires on {eventDate.strftime('%B %d %Y')}\n\n{terms}```\nReact with the checkmark to be notified when the event reminder expires"
        # save a reverence to the message to later retreive the reacions and such
        message = await ctx.send(string)
        await message.add_reaction(u"\u2705")
        # save this event to the dictionary
        curEvent = Event_Reminder(id, ctx.author.id, message.id, message.channel.id , eventDate.month, eventDate.day, eventDate.year, terms)

        # save the event to a file
        file = open(f"{self.eventsDir}{str(year).zfill(4)},{str(month).zfill(2)},{str(day).zfill(2)},{id}.json", "w")
        file.write(dumps(curEvent, default=vars, indent=4))
        file.close()


async def setup(client):
    await client.add_cog(Reminder(client))