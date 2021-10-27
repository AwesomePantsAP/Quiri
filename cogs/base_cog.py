from discord.ext import commands

#commands.cog that requires some setup once the bot is operational
class BaseCog(commands.Cog):
    def __init__(self, client):
        pass
    def setup(self, client):
        pass
