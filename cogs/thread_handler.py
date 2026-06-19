import discord
from discord.ext import commands
import logging
from config import CHANNEL_ID

log = logging.getLogger("jamet")

class ThreadHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        # Ignore if not in the target channel
        if getattr(thread.parent, "id", None) != CHANNEL_ID:
            return

        log.info(f"New thread created: {thread.name} ({thread.id})")
        
        # Give Discord API a second to register the thread creator
        await discord.utils.sleep_until(discord.utils.utcnow())
        
        try:
            owner = thread.owner_id
            if owner:
                await thread.send(f"Woy <@{owner}>, ada yang bisa gue bantu cok? Tanya aja di mari.")
            else:
                await thread.send("Woy! Ada yang bisa gue bantu cok? Tanya aja di mari.")
        except Exception as e:
            log.error(f"Failed to send welcome message in thread {thread.id}: {e}")

async def setup(bot):
    await bot.add_cog(ThreadHandler(bot))