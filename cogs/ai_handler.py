import discord
from discord.ext import commands
import logging
import aiohttp
import re
import time
from config import CHANNEL_ID, LLM_API_URL, LLM_MODEL, LLM_TIMEOUT, RATE_LIMIT_SECONDS, MAX_HISTORY, SOUL_PROMPT
from database import save_message, get_history, prune_history

log = logging.getLogger("jamet")

TRIGGER_KEYWORDS = re.compile(r'\b(met|jam|jamet|jmt|jametai)\b', re.IGNORECASE)

class AIHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rate_limits = {} # (user_id, thread_id) -> timestamp
        self.session = None
        
    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    def check_trigger(self, message):
        if self.bot.user in message.mentions:
            return True
        if TRIGGER_KEYWORDS.search(message.content):
            return True
        return False

    async def call_llm(self, messages):
        payload = {
            "model": LLM_MODEL,
            "messages": messages
        }
        try:
            timeout = aiohttp.ClientTimeout(total=LLM_TIMEOUT)
            async with self.session.post(LLM_API_URL, json=payload, timeout=timeout) as resp:
                if resp.status != 200:
                    log.error(f"LLM API Error: {resp.status} - {await resp.text()}")
                    return None
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
        except aiohttp.ClientError as e:
            log.error(f"LLM API Network Error: {e}")
            return None
        except Exception as e:
            log.error(f"LLM API Unexpected Exception: {e}", exc_info=True)
            return None

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bots and webhooks
        if message.author.bot:
            return
            
        # Ensure it's in a thread
        if not isinstance(message.channel, discord.Thread):
            return
            
        # Ensure the thread's parent is our target channel
        if getattr(message.channel.parent, "id", None) != CHANNEL_ID:
            return
            
        # Check trigger
        if not self.check_trigger(message):
            return

        # Rate Limit check
        user_key = (message.author.id, message.channel.id)
        now = time.time()

        # Evict stale rate limit entries to prevent unbounded memory growth
        self.rate_limits = {k: v for k, v in self.rate_limits.items() if now - v < RATE_LIMIT_SECONDS * 10}

        last_msg_time = self.rate_limits.get(user_key, 0)
        
        if now - last_msg_time < RATE_LIMIT_SECONDS:
            await message.reply("Santai jancuk, ngenteni sitik lah! Ojo kesusu cok.")
            return
            
        self.rate_limits[user_key] = now

        # Fetch history and call LLM
        async with message.channel.typing():
            history = await get_history(message.channel.id, MAX_HISTORY)
            
            # Build payload, conditionally adding current msg if it isn't saved yet
            messages = [{"role": "system", "content": SOUL_PROMPT}] + history + [{"role": "user", "content": message.content}]
            
            reply_text = await self.call_llm(messages)
            
            if reply_text:
                await save_message(message.channel.id, "user", message.content)
                await save_message(message.channel.id, "assistant", reply_text)
                await prune_history(message.channel.id, MAX_HISTORY)
                # Split reply if too long for Discord (max 2000 chars)
                if len(reply_text) > 2000:
                    chunks = [reply_text[i:i+2000] for i in range(0, len(reply_text), 2000)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            await message.channel.send(chunk)
                else:
                    await message.reply(reply_text)
            else:
                await message.reply("Matamu cok, server ra iso konek. Server modyar asu!")

async def setup(bot):
    await bot.add_cog(AIHandler(bot))
