import discord
import asyncio
from discord.ext import commands, tasks
import sqlite3

class Coins(commands.Cog):

    def __init__(self, client):
        self.bot = client
        # the ammount of coins given to a new account
        self.startingCoins = 50
        self.db = sqlite3.connect("/home/pi/Desktop/Justin-bot/coins.db")
        self.cur = self.db.cursor()

        self.wealthyRole = "Wealthy" # the roll to give people who are wealthy

        #self.cur.execute("""DELETE FROM coins WHERE id = :id""",{"coins" : 49, "id" : 663214109726081036})
        #self.db.commit()

        #self.cur.execute("""CREATE TABLE coins (id integer, coins integer)""")
        #self.db.commit()
        # help message for the coins commands
        self.coinsCommands = "```Coins Help: \n !account // makes an account under your name \n !balance // will show the balance of your account \n !balance <@user> // show the balance of the mentioned account \n !pay <@user> <amount> <note> // transfers the given amount of money to the user```"

    @commands.Cog.listener()
    async def on_ready(self):
        print("Coins Cog is ready")

    def getCoins(self, userID):
        '''
        returns the coin balance of an existing account\n
        returns None if the entry does not exist in the database
        '''
        self.cur.execute("SELECT * FROM coins WHERE id=:id",{ "id" : userID})
        result = self.cur.fetchone()
        if result == None:
            self.account(userID)
            return self.getCoins(userID)
        return result[1]

    async def setCoins(self, userID, coins):
        '''
        Sets the coin balance of an existing entry in the database
        '''
        self.cur.execute("""UPDATE coins SET coins = :coins WHERE id = :id""",{"coins" : coins, "id" : userID})
        self.db.commit()
        # this is the only command that changes the coins in the database, so here is a good plce to update the rich people list
        await self.rich()

    async def addCoins(self, userID, coins):
        '''
        Changes the coin balance of an entry by the ammount specified by "coins"\n
        Relies on the setCoin meathod
        '''
        curCoins = self.getCoins(userID)
        await self.setCoins(userID, curCoins+coins)

    def account(self, userID):
        '''
        makes a new entry in the database with the user's unique ID and the starting ammount of coins
        '''

        # make a new row in the database for this user
        self.cur.execute("INSERT INTO coins VALUES (:id, :coins)",{ "id" : userID, "coins" : self.startingCoins})
        self.db.commit()
        


    @commands.command(aliases=["bal"])
    async def balance(self, ctx, member : discord.Member = None):
        author = ctx.message.author
        user = member
        if user == None:

            authorCoins = self.getCoins(author.id)
            if authorCoins == None:
                await ctx.send("you do not have an account, !account to make one.")
                return
            await ctx.send("```"+str(author)+" has a balance of "+str(authorCoins)+" coins.```")

        else:

            userCoins = self.getCoins(user.id)
            if userCoins == None:
                await ctx.send("user does not have an account, they must use !account to make one.")
                return
            await ctx.send("```"+str(user)+" has a balance of "+str(userCoins)+" coins.```")

    @commands.command()
    async def pay(self, ctx, member : discord.Member, coins, *, notes = None):
        coins = int(coins)
        authorID = ctx.message.author.id
        userID = member.id
        if userID == None:
            await ctx.send("invalid recipient")
            return
        authorCoins = self.getCoins(authorID)
        if authorCoins == None:
            await ctx.send("you do not have an account, !account to make one.")
            return
        userCoins = self.getCoins(userID)
        if userCoins == None:
            await ctx.send("the recipient does not have an account, !account to make one.")
            return
        if coins<0:
            await ctx.send("Are you scamming? you just made a big mistake, buddy :smiling_imp:")
            await ctx.send("https://cdn.discordapp.com/attachments/381275218385043468/862167910957318164/image0.png")
            return
        if coins > authorCoins:
            await ctx.send("you're attempting to send more coins than you have, broke boy")
            return
        await self.addCoins(authorID,-coins)
        await self.addCoins(userID,coins)
        if notes:
            await ctx.send("```"+str(ctx.message.author)+" has sent "+str(coins)+" coins to "+str(member)+" \nnotes: "+notes+"```")
        else:
            await ctx.send("```"+str(ctx.message.author)+" has sent "+str(coins)+" coins to "+str(member)+"```")
        return


    async def rich(self):
        '''
        goes through the database and gives the top 25% of coin holders the "wealthy" role
        '''
        # all of the entries in the coin database
        self.cur.execute("SELECT * FROM coins")
        result = self.cur.fetchall()
        avg = self.startingCoins

        for guild in self.bot.guilds:
            role = discord.utils.get(guild.roles, name=self.wealthyRole)
            if(not role):
                print("server \""+str(guild.name)+"\" does not have a wealthy role, making wealthy role \""+self.wealthyRole+"\" now. . .")
                await guild.create_role(name=self.wealthyRole, colour=discord.Colour(0x00ff00))
                print("added \""+self.wealthyRole+"\" role to \""+str(guild.name)+"\"")
                continue
            for user in result:
                # if the number of coins is 1.5 times the average or more
                member = guild.get_member(user[0])
                if(not member):
                    continue
                if(user[1] >= avg*1.5):
                    # give wealthy role
                    await member.add_roles(role)
                else:
                    # take away wealthy role
                    if(role in member.roles):
                        await member.remove_roles(role)

    @commands.command(aliases=["eco", "economy", "coins"])
    async def _eco(self, ctx):
        await ctx.send(self.coinsCommands)

    

def setup(client):
    client.add_cog(Coins(client))