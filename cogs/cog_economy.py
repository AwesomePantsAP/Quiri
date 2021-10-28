from discord.ext import commands
from cogs.base_cog import BaseCog
from cogs.cog_cog_manager import DependencyUnmetError
import traceback

class cog_economy(BaseCog):
    def __init__(self, client):
        db_cog = client.get_cog("cog_database")
        if db_cog is None:
            #raise an exception if it's not present
            raise DependencyUnmetError("Dependency `cog_database` Unmet in `cog_economy!`")

    def setup(self, client):
        #store client
        self.client = client
        #get database cog
        self.db_cog = client.get_cog("cog_database")
        if self.db_cog is None:
            #raise an exception if it's not present
            raise DependencyUnmetError("Dependency `cog_database` Unmet in `cog_economy!`")

        #create the table in the database if it doesn't exist
        create_table_query = """CREATE TABLE IF NOT EXISTS balances (
            balance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            balance INTEGER,
            uuid VARCHAR(18) NOT NULL,
            guild_id VARCHAR(18) NOT NULL
        )
        """
        self.db_cog.do_query(create_table_query)
        self.db_cog.commit()

    #returns true if a balance exists
    def does_balance_exist(self, uuid, guild_id):
        #get the balance
        balance = self.get_balance(uuid, guild_id)
        #return if the balance exists or not
        return balance != None

    #creates a balance totaling balance for user uuid in guild guild_id
    def create_balance(self, balance, uuid, guild_id):
        #check if the balance already exists
        if not self.does_balance_exist(uuid, guild_id):
            #it doesn't exist; create it
            create_balance_query = "INSERT INTO balances(balance, uuid, guild_id) VALUES (?, ?, ?)"
            try:
                self.db_cog.do_query(create_balance_query, (balance, uuid, guild_id))
                self.db_cog.commit()
            except Exception as e:
                #oops, something went wrong creating the balance, print a traceback
                print(traceback.format_exc())
                #return an error message
                return False, "Something went wrong there. Please try again later."

            #return no error messsage
            return True, ""
        else:
            #it exists. return an error message
            return False, "You already have a balance!"

    #changes balance by ammount
    def change_balance(self, ammount, uuid, guild_id):
        #check if the balance already exists
        if self.does_balance_exist(uuid, guild_id):
            change_balance_query = "UPDATE balances SET balance = balance + ? WHERE uuid=? AND guild_id=?"
            try:
                self.db_cog.do_query(change_balance_query, (ammount, uuid, guild_id))
                self.db_cog.commit()
            except Exception as e:
                #oops, something went wrong changing the balance, print a traceback
                print(traceback.format_exc())
                #return an error message
                return False, "Something went wrong there. Please try again later."

            #return no error messsage
            return True, ""
        else:
            #it doesn't exist. return an error message
            return False, "You don't have a balance!"

    #sets the balance to balance
    def set_balance(self, balance, uuid, guild_id):
        #check if the balance already exists
        if self.does_balance_exist(uuid, guild_id):
            set_balance_query = "UPDATE balances SET balance = ? WHERE uuid=? AND guild_id=?"
            try:
                self.db_cog.do_query(set_balance_query, (balance, uuid, guild_id))
                self.db_cog.commit()
            except Exception as e:
                #oops, something went wrong setting the balance, print a traceback
                print(traceback.format_exc())
                #return an error message
                return False, "Something went wrong there. Please try again later."

            #return no error messsage
            return True, ""
        else:
            #it doesn't exist. return an error message
            return False, "You don't have a balance!"

    #gets the balance belonging to uuid in guild_id
    def get_balance(self, uuid, guild_id):
        get_balance_query = "SELECT balance FROM balances WHERE uuid=? AND guild_id=?"
        result = self.db_cog.do_query(get_balance_query, (uuid, guild_id)).fetchone()

        #if it's none, return none
        if isinstance(result, type(None)):
            return None
        #otherwise, it's a tuple; return the first element
        else:
            return result[0]

    #removes a balance entry belonging to uuid in guild_id
    def remove_balance(self, uuid, guild_id):
        #check if the balance already exists
        if self.does_balance_exist(uuid, guild_id):
            remove_balance_query = "DELETE FROM balances WHERE uuid=? AND guild_id=?"
            try:
                return self.db_cog.do_query(remove_balance_query, (uuid, guild_id))
                self.db_cog.commit()
            except Exception as e:
                #oops, something went wrong removing the balance, print a traceback
                print(traceback.format_exc())
                #return an error message
                return False, "Something went wrong there. Please try again later."

            #return no error messsage
            return True, ""
        else:
            #it doesn't exist. return an error message
            return False, "You don't have a balance!"

    @commands.group(pass_context=True, invoke_without_command=True)
    async def economy(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("<@521285684271513601> Implement a help message system already you lazy bitch")

    #creates a balance for the author in the guild
    @economy.command()
    async def createbalance(self, ctx):
        #get the author uuid
        uuid = ctx.author.id
        #get the guild id
        guild_id = ctx.guild.id

        starting_balance = 1000

        #create a balance for the author
        result, error = self.create_balance(starting_balance, uuid, guild_id)

        #inform the user of the result and inform them of their balance
        if result:
            #successfully created balance for the author
            await ctx.send(f"{ctx.author.mention} Successfully created balance: Your balance is ${starting_balance}")
        else:
            #inform the user of the error
            await ctx.send(f"{ctx.author.mention} {error}")

    #get the balance of the author
    @economy.command()
    async def balance(self, ctx):
        #get the author uuid
        uuid = ctx.author.id
        #get the guild id
        guild_id = ctx.guild.id

        #get the balance
        bal = self.get_balance(uuid, guild_id)

        #reply with the balance(if it exists)
        if not bal is None:
            await ctx.send(f"{ctx.author.mention} Your balance is: ${bal}")
        #otherwise, inform the user they do not have a balance
        else:
            await ctx.send(f"{ctx.author.mention} You do not have a balance! Create one with {ctx.bot.command_prefix}economy createbalance")

    #shorthand for !economy balance
    @economy.command()
    async def bal(self, ctx):
        await self.balance(ctx)

    #get the highest balance in the guild
    @economy.command()
    async def baltop(self, ctx, check_users=10):
        #start the final message
        message = "Top balances:```\n"
        #template for a balance entry
        balance_template = "\t{0}. {1}: {2} \n"

        #get the top n balances
        get_balances_query = "SELECT balance, uuid FROM balances WHERE guild_id=? ORDER BY balance"
        result = self.db_cog.do_query(get_balances_query, (ctx.guild.id,))

        if not result is None:
            #iterate through the rows in the result
            i = 1 # entry counter
            for row in result:
                #exit the loop if we've added enough entries
                if i > check_users:
                    break

                balance = row[0] # user balance

                user = await self.client.fetch_user(row[1]) # user
                print(row[1])
                print(user)
                user_fullname = user.name + "#" + user.discriminator # username + discriminator

                #append the formatted entry
                message += balance_template.format(str(i), user_fullname, f"${balance}")

                #increment the counter
                i += 1

            #close the codeblock
            message += "```"
            #send the message
            await ctx.send(message)

    #check another user's balance in the guild
    @economy.command()
    async def checkbalance(self, ctx, user):
        #get the user id
        uuid = user[2:-1]
        #get the guild id
        guild_id = ctx.guild.id

        #get the balance(if it exists)
        if self.does_balance_exist(uuid, guild_id):
            #the user has a balance, get it
            balance = self.get_balance(uuid, guild_id)

            #inform the author of the user's balance
            await ctx.send(f"{ctx.message.author.mention} {user} Has `${balance}`")
        else:
            #the user doesn't have a balance
            await ctx.send(f"{ctx.message.author.mention} {user} Has no balance!")

    #pay user in the guild by amount
    @economy.command()
    async def pay(self, ctx, user, amount):
        pass
