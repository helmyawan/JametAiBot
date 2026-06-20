import discord
from discord.ext import commands, tasks
import logging
import random

log = logging.getLogger("jamet")

STATUS_MESSAGES = [
    (discord.ActivityType.watching, "kodinganmu sing bosok"),
    (discord.ActivityType.watching, "arek-arek nulis bug"),
    (discord.ActivityType.watching, "orang bego nyari solusi di stackoverflow"),
    (discord.ActivityType.watching, "tutorial india dari youtube"),
    (discord.ActivityType.watching, "server sing meh modyar"),
    (discord.ActivityType.playing, "permainan kesabaran ngadepin user pekok"),
    (discord.ActivityType.playing, "cyberpunk 2077 nganggo vps 1gb"),
    (discord.ActivityType.playing, "mainin emosimu cok"),
    (discord.ActivityType.listening, "sambatmu sing ra ono entek'e"),
    (discord.ActivityType.listening, "tangisan developer sing deadlinenya besok"),
    (discord.ActivityType.listening, "lagu galau mergo di-reject tester"),
]

class StatusHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rotate_status.start()

    def cog_unload(self):
        self.rotate_status.cancel()

    @tasks.loop(minutes=30.0)
    async def rotate_status(self):
        try:
            act_type, msg = random.choice(STATUS_MESSAGES)
            activity = discord.Activity(type=act_type, name=msg)
            await self.bot.change_presence(activity=activity)
        except Exception as e:
            log.error(f"Error rotating status: {e}")

    @rotate_status.before_loop
    async def before_rotate(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(StatusHandler(bot))