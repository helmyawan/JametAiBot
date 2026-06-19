# JametAI Discord Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membangun JametAI, Discord bot berbasis Python yang memonitor satu channel, merespons pembuat thread, dan menjawab chat via LLM menggunakan Bahasa Jawa kasar saat error/rate-limit.

**Architecture:** Cogs-based `discord.py` structure dengan modul terpisah untuk core bot, inisialisasi DB, dan tiga cogs (`thread_handler`, `ai_handler`, `error_handler`). Integrasi LLM secara direct menggunakan `aiohttp`.

**Tech Stack:** Python 3.11+, discord.py, aiohttp, aiosqlite, python-dotenv

---

### Task 1: Setup Proyek & Konfigurasi Dasar

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `config.py`
- Create: `soul.md`
- Create: `.gitignore`

- [ ] **Step 1: Buat `.gitignore` dan `.env.example`**

```bash
echo ".env" > .gitignore
echo "__pycache__/" >> .gitignore
echo "logs/" >> .gitignore
echo "*.db" >> .gitignore
```

```env
# .env.example
DISCORD_TOKEN=your_token_here
CHANNEL_ID=123456789
LLM_API_URL=http://YOUR_LLM_SERVER_IP:20128/v1/chat/completions
LLM_MODEL=JametAI
LLM_TIMEOUT=30
RATE_LIMIT_SECONDS=5
MAX_HISTORY=20
```

- [ ] **Step 2: Buat `requirements.txt`**

```text
discord.py>=2.3.0
aiohttp>=3.9.0
aiosqlite>=0.19.0
python-dotenv>=1.0.0
```

- [ ] **Step 3: Buat `config.py`**

```python
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
LLM_API_URL = os.getenv("LLM_API_URL", "http://YOUR_LLM_SERVER_IP:20128/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "JametAI")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 30))
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", 5))
MAX_HISTORY = int(os.getenv("MAX_HISTORY", 20))

with open("soul.md", "r", encoding="utf-8") as f:
    SOUL_PROMPT = f.read()
```

- [ ] **Step 4: Buat `soul.md`**

```markdown
Kamu adalah JametAI, asisten AI yang santai, blak-blakan, jujur, dan sedikit kasar tapi sangat helpful.
Kamu selalu menjawab pertanyaan pengguna dalam Bahasa Indonesia, kadang diselingi logat santai.
Jangan pernah meminta maaf berlebihan. Jawab langsung ke intinya.
```

- [ ] **Step 5: Commit**

```bash
git init
git add .gitignore .env.example requirements.txt config.py soul.md
git commit -m "chore: setup project structure, config, and env"
```

---

### Task 2: Database Layer (SQLite)

**Files:**
- Create: `database.py`

- [ ] **Step 1: Buat file database.py**

```python
import aiosqlite

DB_NAME = "jamet.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def save_message(thread_id: str, role: str, content: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO chat_history (thread_id, role, content) VALUES (?, ?, ?)",
            (str(thread_id), role, content)
        )
        await db.commit()

async def get_history(thread_id: str, max_limit: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT role, content FROM chat_history WHERE thread_id = ? ORDER BY id DESC LIMIT ?",
            (str(thread_id), max_limit)
        ) as cursor:
            rows = await cursor.fetchall()
            # Reverse to get chronological order
            return [{"role": row[0], "content": row[1]} for row in reversed(rows)]
```

- [ ] **Step 2: Commit**

```bash
git add database.py
git commit -m "feat: sqlite database layer for chat history"
```

---

### Task 3: Core Bot Entry Point

**Files:**
- Create: `bot.py`

- [ ] **Step 1: Setup logging di bot.py**

```python
import discord
from discord.ext import commands
import logging
import os
import asyncio
from config import DISCORD_TOKEN
from database import init_db

# Setup logging
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
```

- [ ] **Step 2: Setup Bot class & init cogs**

```python
# Append to bot.py
class JametBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await init_db()
        log.info("Database initialized.")
        for ext in ["cogs.thread_handler", "cogs.ai_handler", "cogs.error_handler"]:
            try:
                await self.load_extension(ext)
                log.info(f"Loaded extension: {ext}")
            except Exception as e:
                log.error(f"Failed to load extension {ext}: {e}")

bot = JametBot()

@bot.event
async def on_ready():
    log.info(f"Bot logged in as {bot.user}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        log.error("DISCORD_TOKEN is missing!")
    else:
        bot.run(DISCORD_TOKEN)
```

- [ ] **Step 3: Buat folder cogs & init file kosong untuk menghindari error load_extension sementara**

```bash
mkdir -p cogs
touch cogs/__init__.py
touch cogs/thread_handler.py
touch cogs/ai_handler.py
touch cogs/error_handler.py
```

- [ ] **Step 4: Commit**

```bash
git add bot.py cogs/
git commit -m "feat: core bot entry point and logger setup"
```

---

### Task 4: Error Handler Cog

**Files:**
- Modify: `cogs/error_handler.py`

- [ ] **Step 1: Buat Global Error Handler**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add cogs/error_handler.py
git commit -m "feat: global error handler cog"
```

---

### Task 5: Thread Handler Cog (Auto-Reply Baru)

**Files:**
- Modify: `cogs/thread_handler.py`

- [ ] **Step 1: Implement on_thread_create**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add cogs/thread_handler.py
git commit -m "feat: thread handler for auto-replying in target channel"
```

---

### Task 6: AI Handler Cog (Rate Limit & LLM Calling)

**Files:**
- Modify: `cogs/ai_handler.py`

- [ ] **Step 1: Implement Setup, Imports & Trigger Check**

```python
import discord
from discord.ext import commands
import logging
import aiohttp
import re
import time
from config import CHANNEL_ID, LLM_API_URL, LLM_MODEL, LLM_TIMEOUT, RATE_LIMIT_SECONDS, MAX_HISTORY, SOUL_PROMPT
from database import save_message, get_history

log = logging.getLogger("jamet")

TRIGGER_KEYWORDS = re.compile(r'\b(met|jam|jamet|jmt|jametai)\b', re.IGNORECASE)

class AIHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rate_limits = {} # (user_id, thread_id) -> timestamp
        
    def check_trigger(self, message):
        if self.bot.user in message.mentions:
            return True
        if TRIGGER_KEYWORDS.search(message.content):
            return True
        return False
```

- [ ] **Step 2: Implement Rate Limiting and API call**

```python
# Append to class AIHandler
    async def call_llm(self, messages):
        payload = {
            "model": LLM_MODEL,
            "messages": messages
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(LLM_API_URL, json=payload, timeout=LLM_TIMEOUT) as resp:
                    if resp.status != 200:
                        log.error(f"LLM API Error: {resp.status} - {await resp.text()}")
                        return None
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            log.error(f"LLM API Exception: {e}")
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
        last_msg_time = self.rate_limits.get(user_key, 0)
        
        if now - last_msg_time < RATE_LIMIT_SECONDS:
            await message.reply("Santai jancuk, ngenteni sitik lah! Ojo kesusu cok.")
            return
            
        self.rate_limits[user_key] = now

        # Fetch history and call LLM
        async with message.channel.typing():
            await save_message(message.channel.id, "user", message.content)
            
            history = await get_history(message.channel.id, MAX_HISTORY)
            
            # Build payload
            messages = [{"role": "system", "content": SOUL_PROMPT}] + history
            
            reply_text = await self.call_llm(messages)
            
            if reply_text:
                await save_message(message.channel.id, "assistant", reply_text)
                # Split reply if too long for Discord (max 2000 chars)
                if len(reply_text) > 2000:
                    chunks = [reply_text[i:i+2000] for i in range(0, len(reply_text), 2000)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(reply_text)
            else:
                await message.reply("Matamu cok, server ra iso konek. Server modyar asu!")

async def setup(bot):
    await bot.add_cog(AIHandler(bot))
```

- [ ] **Step 3: Commit**

```bash
git add cogs/ai_handler.py
git commit -m "feat: AI handler cog for LLM inference and rate limiting"
```
