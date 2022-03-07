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

        self.db = sqlite3.connect("/home/pi/Justin-bot/coins.db")
        self.cur = self.db.cursor()

        try:
            self.cur.execute("""CREATE TABLE coins (id integer, coins integer)""")
            self.db.commit()
            print("making and using a new database")
        except:
            print("using existing coins database")

        self.wealthyRole = "Wealthy" # the roll to give people who are wealthy
        self.poorRole = "Poor" # the roll to give people who are poor!

        # list to keep track of robbery cooldowns
        self.robList = {}
        # how long is the robbery cooldown in seconds (3600 seconds per hour)
        self.robCooldown = 3600*12

        # list to keep track of flexing cooldowns
        self.flexList = {}
        # how long is the flexing cooldown in seconds (3600 seconds per hour)
        self.flexCooldown = 3600*2

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
        
    @commands.command(aliases=["beat"])
    async def flex(self, ctx, member : discord.Member = None):
        author = ctx.message.author
        if member.id == None:
            await ctx.send("invalid person")
            return      

        if ctx.author.voice is None:
            return await ctx.send("You're not in a voice channel.")

        call = ctx.author.voice.channel

        if member.voice is None:
            return await ctx.send("You have to be in the same call as the target.")

        if member.voice.channel != call:
            return await ctx.send("You have to be in the same call as the target.")

        guild = ctx.guild
        wealthyRole = discord.utils.get(guild.roles, name=self.wealthyRole)
        if(wealthyRole not in author.roles):
            return await ctx.send("broke bitch! only wealthy people can flex")

        # if this person has never before flexed on someone
        if not author.id in self.flexList:
            self.flexList[author.id] = 0
        # if the time since their last flex is less then the cooldown
        if time.time() - self.flexList[author.id] < self.robCooldown: 
            # how long till they can flex again
            timeTillFlex = time.gmtime(self.flexCooldown - (time.time() - self.flexList[author.id]))
            timeTillFlexStr = (str(timeTillFlex.tm_hour)+" hours ")+(str(timeTillFlex.tm_min)+" minutes ")
            # tell them off
            return await ctx.send("yo bitch ass can't flex for another "+timeTillFlexStr)
        # set this as the last time they flexed
        self.flexList[author.id] = time.time()
        # send some funny message
        channel = self.bot.get_channel(830510114016329818)
        await member.move_to(channel)
        await ctx.send("Goodbye "+member.mention+", send me a postscard from blocksville.")
        return await ctx.send("https://tenor.com/view/dedrick-williams-dedrick-flex-dedrick-xxx-xxxtentacion-xxxtentacion-killer-gif-22346694")


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

        # if they tried to rob justinbot
        if member.id == 663214109726081036:
            await ctx.send("?????????????????????????????????")
            time.sleep(3)
            return await ctx.send("https://cdn.discordapp.com/attachments/476896177900486676/898855743510433802/69e48529b5dc35ebb8efe26e11aa929729c5d4f3046744c4c7583a383892b0d1_1-1.mp4")
        
        # set this as the last time they robbed
        self.robList[author.id] = time.time()
        # 60% chance of sucess
        if random.random() > 0.6:
            return await ctx.send("you failed to rob "+str(member))
        authorCoins = self.getCoins(author.id)
        userCoins = self.getCoins(member.id)
        # get te diff between the attacker and victim. then divide by 500
        coinDiff = ((userCoins)-authorCoins)/self.startingCoins
        # multiply by 5 to get a sizable ammount of coins
        coinDiff = (coinDiff * 5)
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
    async def tyranny(self,ctx,member : discord.Member, coins):
        if ctx.author.id != 260671074763669504:
            return await ctx.send("yo mama")
        await self.setCoins(member.id,coins)

    @commands.command()
    async def leaderboard(self, ctx):
        leaderString = "```"
        guild = ctx.guild

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
            leaderString += "#"+str(rank)+": "+"{:<16}".format(str(member.name))+" ¢"+str(user[1])+"\n"
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
            
            #calculate standard dev
            std_sum = 0
            num_people = 0
            for user in result:
                member = guild.get_member(user[0])
                # only count people in this server
                if(not member):
                    continue
                # count up people and the sum for standard deviation
                num_people += 1
                std_sum += (user[1] - avg) ** 2
            std = (std_sum / (num_people - 1)) ** 0.5

            for user in result:
                member = guild.get_member(user[0])
                if(not member):
                    continue

                # this user's number of standard deviations from the average
                user_deviation = (user[1] - avg)/std

                # if this user is 1 standard deviations below average
                if(user_deviation <= -1):
                    # give poor role
                    await member.add_roles(poorRole)
                else:
                    # take away poor role
                    if(poorRole in member.roles):
                        await member.remove_roles(poorRole)
                # if this users is 1 standard deviation above average
                if(user_deviation >= 1):
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
