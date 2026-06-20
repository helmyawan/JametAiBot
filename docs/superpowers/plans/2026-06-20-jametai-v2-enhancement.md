# JametAI V2 Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement dynamic status rotation, typing UX enhancement, file attachment reading, and global user reputation tracking via SQLite for JametAI.

**Architecture:** Adds `cogs/status_handler.py` for dynamic status loop. Enhances `cogs/ai_handler.py` with attachment downloading and delayed chunking. Extends `database.py` with `user_reputation` table and integrates it into the LLM payload.

**Tech Stack:** Python 3.11+, discord.py, aiohttp, aiosqlite

---

### Task 1: Database Schema for User Reputation

**Files:**
- Modify: `database.py`

- [ ] **Step 1: Add user_reputation table and queries**

```python
# In database.py, update init_db:
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
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_reputation (
                user_id TEXT PRIMARY KEY,
                notes TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute("CREATE INDEX IF NOT EXISTS idx_thread_id ON chat_history(thread_id)")
        await db.commit()

# Add new functions:
async def get_user_reputation(user_id: str) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT notes FROM user_reputation WHERE user_id = ?", (str(user_id),)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""

async def update_user_reputation(user_id: str, notes: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO user_reputation (user_id, notes, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET notes=excluded.notes, updated_at=CURRENT_TIMESTAMP
        ''', (str(user_id), notes))
        await db.commit()
```

- [ ] **Step 2: Commit changes**

```bash
git add database.py
git commit -m "feat: add user_reputation table and queries"
```

---

### Task 2: File Attachment Reader

**Files:**
- Modify: `cogs/ai_handler.py`

- [ ] **Step 1: Implement file reading logic in AIHandler**

Add `process_attachments` to `AIHandler`:

```python
# In cogs/ai_handler.py, inside class AIHandler:
    async def process_attachments(self, message) -> str:
        if not message.attachments:
            return ""
            
        allowed_exts = {'.py', '.js', '.ts', '.html', '.css', '.txt', '.json', '.md', '.csv', '.sh', '.yaml', '.yml'}
        max_size = 50 * 1024  # 50KB
        
        file_contents = []
        for att in message.attachments:
            ext = "." + att.filename.split('.')[-1].lower() if '.' in att.filename else ""
            if ext not in allowed_exts:
                continue
                
            if att.size > max_size:
                await message.reply(f"Matamu! File `{att.filename}` kegeden cok, maksimal 50KB wae. Males moco aku.")
                continue
                
            try:
                content = await att.read()
                text_content = content.decode('utf-8')
                file_contents.append(f"\n\n--- Isi File: {att.filename} ---\n{text_content}\n--- End File ---")
            except Exception as e:
                log.error(f"Failed to read attachment {att.filename}: {e}")
                
        return "".join(file_contents)
```

- [ ] **Step 2: Use in `on_message`**

```python
# In cogs/ai_handler.py, update on_message before rate limit check:

        # Check trigger
        if not self.check_trigger(message):
            return

        # Fetch file content if any
        attachment_text = await self.process_attachments(message)
        final_user_content = message.content + attachment_text

        # Rate Limit check
```

Modify the payload builder to use `final_user_content`:
```python
        # In on_message, update the payload builder:
            # Build payload, conditionally adding current msg if it isn't saved yet
            messages = [{"role": "system", "content": SOUL_PROMPT}] + history + [{"role": "user", "content": final_user_content}]
```

And update the save call:
```python
            if reply_text:
                await save_message(message.channel.id, "user", final_user_content)
```

- [ ] **Step 3: Commit changes**

```bash
git add cogs/ai_handler.py
git commit -m "feat: support reading text file attachments"
```

---

### Task 3: Global User Memory Injection & Background Update

**Files:**
- Modify: `cogs/ai_handler.py`

- [x] **Step 1: Import DB functions and asyncio**
- [x] **Step 2: Inject Reputation into Context**
- [x] **Step 3: Create Background Updater Function**
- [x] **Step 4: Trigger Background Update**
- [x] **Step 5: Commit changes**

```bash
git add cogs/ai_handler.py
git commit -m "feat: global user memory injection and background updating"
```

---

### Task 4: Enhanced UX (Typing Delay on Chunks)

**Files:**
- Modify: `cogs/ai_handler.py`

- [ ] **Step 1: Add delay and typing to multi-chunk responses**

```python
# In on_message, update the chunk sending logic:
                # Split reply if too long for Discord (max 2000 chars)
                if len(reply_text) > 2000:
                    chunks = [reply_text[i:i+2000] for i in range(0, len(reply_text), 2000)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            async with message.channel.typing():
                                await asyncio.sleep(1) # Fake typing delay for UX
                            await message.channel.send(chunk)
                else:
                    await message.reply(reply_text)
```

- [ ] **Step 2: Commit changes**

```bash
git add cogs/ai_handler.py
git commit -m "feat: add typing delay UX between long response chunks"
```

---

### Task 5: Dynamic Status Rotator

**Files:**
- Create: `cogs/status_handler.py`

- [ ] **Step 1: Create the StatusHandler Cog**

```python
import discord
from discord.ext import commands, tasks
import logging
import random

log = logging.getLogger("jamet")

STATUS_MESSAGES = [
    # Watching
    (discord.ActivityType.watching, "kodinganmu sing bosok"),
    (discord.ActivityType.watching, "arek-arek nulis bug"),
    (discord.ActivityType.watching, "orang bego nyari solusi di stackoverflow"),
    (discord.ActivityType.watching, "tutorial india dari youtube"),
    (discord.ActivityType.watching, "server sing meh modyar"),
    # Playing
    (discord.ActivityType.playing, "permainan kesabaran ngadepin user pekok"),
    (discord.ActivityType.playing, "cyberpunk 2077 nganggo vps 1gb"),
    (discord.ActivityType.playing, "mainin emosimu cok"),
    # Listening
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
```

- [ ] **Step 2: Add it to bot.py**

```python
# In bot.py, update the load_extension array:
        for ext in ["cogs.thread_handler", "cogs.ai_handler", "cogs.error_handler", "cogs.status_handler"]:
```

- [ ] **Step 3: Commit changes**

```bash
git add cogs/status_handler.py bot.py
git commit -m "feat: dynamic status rotator with sarcastic messages"
```
