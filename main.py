import os
import asyncio
# load our local env so we dont have the token in public
from discord.ext import commands
from discord.ext.commands import CommandNotFound

from cogs import cog_cog_manager

client = commands.Bot(command_prefix='!')  # prefix our commands with '!'

#load cogs
cog_manager = cog_cog_manager.cog_cog_manager(
    client,
    "cog_database"
)

@client.event  # check if bot is ready
async def on_ready():
    print('Bot online')

    #setup all managed cogs
    cog_manager.setup()

# command to clear channel messages
@client.command()
async def clear(ctx, amount=5):
    #purge messages with limit limit
    await ctx.channel.purge(limit=amount)
    await ctx.send("Cleared! :broom::wind:")

#catch invalid commands
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send(f"Invalid command: `{ctx.message.content}`")
    raise error

#get the bot token
token_file = open("token.txt")
token = token_file.read()

#start the bot
client.run(token)
