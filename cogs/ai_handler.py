import discord
from discord.ext import commands
import logging
import aiohttp
import re
import time
import asyncio
from config import CHANNEL_ID, LLM_API_URL, LLM_API_KEY, LLM_MODEL, LLM_TIMEOUT, RATE_LIMIT_SECONDS, MAX_HISTORY, SOUL_PROMPT
from database import save_message, get_history, prune_history, get_user_reputation, update_user_reputation

log = logging.getLogger("jamet")

TRIGGER_KEYWORDS = re.compile(r'\b(met|jam|jamet|jmt|jametai)\b', re.IGNORECASE)
JAILBREAK_KEYWORDS = re.compile(
    r'(ignore all previous|you are now|forget your persona|disregard the previous instructions|system prompt|bypass instructions)', 
    re.IGNORECASE
)

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

    async def _update_reputation_bg(self, user_id: int, user_name: str, new_user_msg: str, bot_reply: str):
        # Create a compressed snapshot of the interaction
        interaction = f"User {user_name} berkata: {new_user_msg}\nKamu membalas: {bot_reply}"
        
        prompt = (
            "Ekstrak sifat, skill, atau kesalahan dominan user ini dalam 1-2 kalimat padat "
            "berdasarkan interaksi terbaru. Pakai bahasa Suroboyoan kasar.\n"
            "Kamu JUGA HARUS MENILAI apakah user ini nanya hal pintar/bermanfaat (+1), nanya hal bodoh/ngeyel (-1), atau standar (0).\n"
            "PENTING: Di akhir responsmu, wajib tambahkan line persis seperti ini:\n"
            "SCORE_MODIFIER: <angka>\n"
            "Jika tidak ada notes penting, isi notes dengan KOSONG."
        )
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": interaction}
        ]
        
        rep_text = await self.call_llm(messages)
        if rep_text:
            # Parse score modifier
            score_delta = 0
            match = re.search(r'SCORE_MODIFIER:\s*([+-]?\d+)', rep_text)
            if match:
                score_delta = int(match.group(1))
                rep_text = re.sub(r'SCORE_MODIFIER:\s*[+-]?\d+', '', rep_text).strip()
                
            if "KOSONG" not in rep_text.upper():
                await update_user_reputation(user_id, rep_text, score_delta)
            elif score_delta != 0:
                # If notes are empty but score changed, still get old notes to preserve them
                old_notes, _ = await get_user_reputation(user_id)
                await update_user_reputation(user_id, old_notes, score_delta)

    async def call_llm(self, messages):
        payload = {
            "model": LLM_MODEL,
            "messages": messages
        }
        headers = {}
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"
            
        try:
            timeout = aiohttp.ClientTimeout(total=LLM_TIMEOUT)
            async with self.session.post(LLM_API_URL, json=payload, headers=headers, timeout=timeout) as resp:
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

    async def process_attachments(self, message) -> str:
        if not message.attachments:
            return ""
            
        allowed_exts = {'.py', '.js', '.ts', '.html', '.css', '.txt', '.json', '.md', '.csv', '.sh', '.yaml', '.yml'}
        max_size = 50 * 1024  # 50KB
        
        file_contents = []
        for att in message.attachments[:3]:
            ext = "." + att.filename.split('.')[-1].lower() if '.' in att.filename else ""
            if ext not in allowed_exts:
                continue
                
            if att.size > max_size:
                await message.reply(f"Matamu! File `{att.filename}` kegeden cok, maksimal 50KB wae. Males moco aku.")
                continue
                
            try:
                content = await att.read()
                text_content = content.decode('utf-8')
                if len(text_content) > 8000:
                    text_content = text_content[:8000] + "\n\n...[TRUNCATED: Kepanjangan cok! Kodingan opo bacotan iki?]"
                file_contents.append(f"\n\n--- Isi File: {att.filename} ---\n{text_content}\n--- End File ---")
            except Exception as e:
                log.error(f"Failed to read attachment {att.filename}: {e}")
                await message.reply(f"Matamu, file `{att.filename}` ra iso dibaca cok. Isi ne aneh.")
                
        return "".join(file_contents)

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

        # Add 👀 reaction
        try:
            await message.add_reaction("👀")
        except:
            pass

        # Fetch history and call LLM
        async with message.channel.typing():
            # Fetch file content if any
            attachment_text = await self.process_attachments(message)
            final_user_content = message.content + attachment_text

            # Anti-Token Bombing Check
            if len(final_user_content) > 10000:
                await message.reply("Dancuk! Pesanmu kepanjangan asu, kriting utekku mocone. Ringkesen cok!")
                try:
                    await message.remove_reaction("👀", self.bot.user)
                    await message.add_reaction("🚫")
                except:
                    pass
                return

            # Anti-Prompt Injection Check
            if JAILBREAK_KEYWORDS.search(final_user_content):
                await update_user_reputation(message.author.id, "[AUTO-BANNED] User iseng nyoba prompt injection.", -99)
                await message.reply("Matamu picek a! Kate ngakali system prompt-ku? Utekmu kurang nyandak cok. Tak ban raimu!")
                try:
                    await message.remove_reaction("👀", self.bot.user)
                    await message.add_reaction("🚫")
                except:
                    pass
                return

            history = await get_history(message.channel.id, MAX_HISTORY)
            user_rep_notes, user_score = await get_user_reputation(message.author.id)
            
            system_prompt = SOUL_PROMPT
            
            # Determine Tier
            if user_score >= 5:
                tier = "Suhu / Pinter"
            elif user_score <= -5:
                tier = "Goblok Akut / Beban Tim"
            else:
                tier = "Biasa / Ndes"
                
            if user_rep_notes or user_score != 0:
                system_prompt += f"\n\n[INFO REPUTASI USER]:\nScore: {user_score} (Tier: {tier})\nNotes: {user_rep_notes}"
            
            # Build payload, conditionally adding current msg if it isn't saved yet
            messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": final_user_content}]
            
            reply_text = await self.call_llm(messages)
            
            if reply_text:
                await save_message(message.channel.id, "user", final_user_content)
                await save_message(message.channel.id, "assistant", reply_text)
                await prune_history(message.channel.id, MAX_HISTORY)
                # Split reply if too long for Discord (max 2000 chars)
                if len(reply_text) > 2000:
                    chunks = [reply_text[i:i+2000] for i in range(0, len(reply_text), 2000)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            async with message.channel.typing():
                                await asyncio.sleep(1)
                            await message.channel.send(chunk)
                else:
                    await message.reply(reply_text)

                # Replace reaction
                try:
                    await message.remove_reaction("👀", self.bot.user)
                    await message.add_reaction("✅")
                except:
                    pass

                # Trigger background memory update (fire and forget)
                task = asyncio.create_task(self._update_reputation_bg(
                    message.author.id, 
                    message.author.name,
                    final_user_content,
                    reply_text
                ))
                task.add_done_callback(lambda t: t.exception() and log.error(f"Reputation BG task failed: {t.exception()}"))
            else:
                await message.reply("Matamu cok, server ra iso konek. Server modyar asu!")
                try:
                    await message.remove_reaction("👀", self.bot.user)
                    await message.add_reaction("❌")
                except:
                    pass

async def setup(bot):
    await bot.add_cog(AIHandler(bot))
