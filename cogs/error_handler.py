import discord
from discord.ext import commands
import logging

log = logging.getLogger("jamet")

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        log.error(f"Command error: {error}")

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        log.error(f"Error in event {event}", exc_info=True)

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
