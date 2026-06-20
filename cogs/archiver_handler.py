import discord
from discord.ext import commands, tasks
import logging
from config import CHANNEL_ID

log = logging.getLogger("jamet")

class ArchiverHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.archive_threads.start()

    def cog_unload(self):
        self.archive_threads.cancel()

    @tasks.loop(hours=6.0)
    async def archive_threads(self):
        try:
            channel = self.bot.get_channel(CHANNEL_ID)
            if not channel or not isinstance(channel, discord.TextChannel):
                return
                
            for thread in channel.threads:
                if thread.archived:
                    continue
                    
                # Get last message time (fallback to thread creation if no messages)
                last_active = thread.archive_timestamp
                if thread.last_message_id:
                    try:
                        msg = await thread.fetch_message(thread.last_message_id)
                        last_active = msg.created_at
                    except:
                        pass
                
                if not last_active:
                    continue
                    
                # 3 days = 72 hours
                delta = discord.utils.utcnow() - last_active
                if delta.total_seconds() > 72 * 3600:
                    try:
                        await thread.send("Wes 3 dino ra ono sing cangkruk neng kene. Thread iki tak kubur wae cok. Modyar o kono.")
                        await thread.edit(archived=True, reason="Auto-archived due to 3 days of inactivity")
                        log.info(f"Auto-archived thread: {thread.name}")
                    except Exception as e:
                        log.error(f"Failed to archive thread {thread.id}: {e}")
        except Exception as e:
            log.error(f"Error in archive loop: {e}")

    @archive_threads.before_loop
    async def before_archive(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ArchiverHandler(bot))