import discord
from discord.ext import commands
import sqlite3
import random
import time

class Coins(commands.Cog):

    def __init__(self, client):
        self.bot = client
        # the ammount of coins given to a new account
        self.startingCoins = 500
        self.db = sqlite3.connect("/home/pi/Desktop/Justin-bot/coins.db")
        self.cur = self.db.cursor()

        self.wealthyRole = "Wealthy" # the roll to give people who are wealthy
        self.poorRole = "Poor" # the roll to give people who are poor!

        # list to keep track of robbery cooldowns
        self.robList = {}
        # how long is the robbery cooldown in seconds (3600 seconds per hour)
        self.robCooldown = 3600*12

        # help message for the coins commands
        self.coinsCommands = "```Coins Help: \n!balance // will show the balance of your account \n!balance <@user> // show the balance of the mentioned account \n!pay <@user> <amount> <note> // transfers the given amount of money to the user```"

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
        await self.setCoins(userID, round(curCoins+coins))

    def account(self, userID):
        '''
        makes a new entry in the database with the user's unique ID and the starting ammount of coins
        '''

        # make a new row in the database for this user
        self.cur.execute("INSERT INTO coins VALUES (:id, :coins)",{ "id" : userID, "coins" : self.startingCoins})
        self.db.commit()
        
    @commands.command(aliases=["childSupport"])
    async def rob(self, ctx, member : discord.Member = None):
        author = ctx.message.author
        if member.id == None:
            await ctx.send("invalid person")
            return      

        # if this person has never before robbed someone
        if not author.id in self.robList:
            self.robList[author.id] = 0
        # if the time since their last rob is less then the cooldown
        if time.time() - self.robList[author.id] < self.robCooldown: 
            # how long till they can rob again
            timeTillRob = time.gmtime(self.robCooldown - (time.time() - self.robList[author.id]))
            timeTillRobStr = (str(timeTillRob.tm_hour)+" hours ")+(str(timeTillRob.tm_min)+" minutes ")
            # tell them off
            return await ctx.send("yo bitch ass can't rob people for another "+timeTillRobStr)
        # set this as the last time they robbed
        self.robList[author.id] = time.time()
        # 60% chance of sucess
        if random.random() > 0.6:
            return await ctx.send("you failed to rob "+str(member))
        authorCoins = self.getCoins(author.id)
        userCoins = self.getCoins(member.id)
        # get te diff between the attacker and victim. reduce the victim's wealth to nerf rich ppl. then devide by 500
        coinDiff = ((userCoins*0.75)-authorCoins)/self.startingCoins
        # multiply by 10 to get a sizable ammount of coins
        coinDiff = (coinDiff * 10)
        # make the diff the center of a normal distribution to add some randomness to the system
        gain = round(random.gauss(coinDiff,3))
        # affect the coins of each party
        await self.addCoins(author.id,gain)
        await self.addCoins(member.id,-gain)
        # send some funny gain/loss messages
        if gain > 0:
            await ctx.send("you got the bag and stole "+str(abs(gain))+" kazzoins from "+str(member))
            return await ctx.send("https://tenor.com/view/gun-firing-shooting-mask-gang-gif-17710088")
        else:
            await ctx.send("you fumbled the bag and lost "+str(abs(gain))+" kazzoins to "+str(member))
            return await ctx.send("https://tenor.com/view/namztaes-sad-crying-boonk-gang-gif-23232403")        


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

    @commands.command()
    async def leaderboard(self, ctx):
        leaderString = "```"
        guild = ctx.guild
        leaderBoard = []

        # all of the entries in the coin database and put it in result
        self.cur.execute("SELECT * FROM coins")
        result = self.cur.fetchall()

        result.sort(reverse=True, key=lambda y: y[1])

        rank = 1
        for user in result:
            member = guild.get_member(user[0])
            # if the user is not in this server
            if(not member):
                continue
            leaderString += "#"+str(rank)+": "+"{:<15}".format(str(member.name))+" ¢"+str(user[1])+"\n"
            rank += 1
        
        return await ctx.send(leaderString+"```")


    async def rich(self):
        '''
        goes through the database and gives the top 25% of coin holders the "wealthy" role
        '''
        # all of the entries in the coin database
        self.cur.execute("SELECT * FROM coins")
        result = self.cur.fetchall()
        avg = self.startingCoins

        for guild in self.bot.guilds:
            wealthyRole = discord.utils.get(guild.roles, name=self.wealthyRole)
            poorRole = discord.utils.get(guild.roles, name=self.poorRole)
            if(not wealthyRole):
                print("server \""+str(guild.name)+"\" does not have a wealthy role, making wealthy role \""+self.wealthyRole+"\" now. . .")
                await guild.create_role(name=self.wealthyRole, colour=discord.Colour(0x00ff00))
                print("added \""+self.wealthyRole+"\" role to \""+str(guild.name)+"\"")
                continue
            if(not poorRole):
                print("server \""+str(guild.name)+"\" does not have a poor role, making poor role \""+self.poorRole+"\" now. . .")
                await guild.create_role(name=self.poorRole, colour=discord.Colour(0x8A6430))
                print("added \""+self.poorRole+"\" role to \""+str(guild.name)+"\"")
                continue
            
            for user in result:
                member = guild.get_member(user[0])
                # if the number of coins is 0.5 times the average or less
                if(not member):
                    continue
                if(user[1] <= avg*0.5):
                    # give poor role
                    await member.add_roles(poorRole)
                else:
                    # take away poor role
                    if(poorRole in member.roles):
                        await member.remove_roles(poorRole)
                # if the number of coins is 1.5 times the average or more
                if(user[1] >= avg*1.5):
                    # give wealthy role
                    await member.add_roles(wealthyRole)
                else:
                    # take away wealthy role
                    if(wealthyRole in member.roles):
                        await member.remove_roles(wealthyRole)

    @commands.command(aliases=["eco", "economy", "coins"])
    async def _eco(self, ctx):
        await ctx.send(self.coinsCommands)

    

def setup(client):
    client.add_cog(Coins(client))
