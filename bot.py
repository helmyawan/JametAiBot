import discord
from discord.ext import commands
import logging
import os
from config import DISCORD_TOKEN
from database import init_db

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/jamet.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("jamet")

class JametBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await init_db()
        log.info("Database initialized.")
        for ext in ["cogs.thread_handler", "cogs.ai_handler", "cogs.error_handler", "cogs.status_handler", "cogs.archiver_handler", "cogs.slash_commands"]:
            try:
                await self.load_extension(ext)
                log.info(f"Loaded extension: {ext}")
            except Exception as e:
                log.error(f"Failed to load extension {ext}: {e}")
        
        # Sync slash commands
        await self.tree.sync()
        log.info("Slash commands synced.")

bot = JametBot()

@bot.event
async def on_ready():
    log.info(f"Bot logged in as {bot.user}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        log.error("DISCORD_TOKEN is missing!")
    else:
        bot.run(DISCORD_TOKEN)
