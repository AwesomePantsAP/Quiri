from discord.ext import commands
import sqlite3
from cogs.base_cog import BaseCog

class cog_database(BaseCog):
    #gets the database and checks that all servers have entries in the "servers" table
    def setup(self, client):
        #get the database connection
        self.connection = sqlite3.connect("db.sqlite3")

        #create the guilds table if it doesn't exist
        create_table_query = """CREATE TABLE IF NOT EXISTS guilds (
            guild_id VARCHAR(18) PRIMARY KEY NOT NULL UNIQUE,
            guild_name VARCHAR(64) NOT NULL
        )
        """
        self.do_query(create_table_query)

        #iterate through the guilds the bot is in and ensure they have an entry
        #in the `guilds` table
        for guild in client.guilds:
            print(f"DatabaseCog >>> Checking record for {guild.id}::`{guild.name}`")
            guild_record = self.do_query("SELECT * FROM guilds WHERE guild_id = ?;", (str(guild.id),)).fetchone()

            #is the record an instance of cursor?
            if isinstance(guild_record, type(None)):
                #yes, the result is None(it can't be multiple)
                #the record doesn't exist, add one
                print("\tNo record found: Creating record")
                self.do_query("INSERT INTO guilds VALUES (?, ?)", (str(guild.id), guild.name))
                self.connection.commit()
                guild_record = self.do_query("SELECT * FROM guilds WHERE guild_id = ?;", (str(guild.id),)).fetchone()
                print(f"\tRecord Created: {guild_record}")
            else:
                #otherwise we don't need to do anything
                print(f"\tRecord found: {guild_record}")

    #executes query on database
    def do_query(self, query, arguments=()):
        cursor = self.connection.cursor()
        return cursor.execute(query, arguments)

    #commits changes done to the database
    def commit(self):
        self.connetion.commit()
