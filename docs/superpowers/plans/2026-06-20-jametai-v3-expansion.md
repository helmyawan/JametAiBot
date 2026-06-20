# JametAI V3 Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Auto-Archiver, Senior Dev Mode, Gamified Reputation Score, Reaction UX (👀 to ✅), and Slash Commands.

**Architecture:** Modifies existing config, DB schema, and AI handler. Adds two new cogs: `archiver_handler` and `slash_commands`.

**Tech Stack:** Python 3.11+, discord.py (app_commands), aiosqlite

---

### Task 1: Environment & Config Updates

**Files:**
- Modify: `.env.example`
- Modify: `config.py`

- [ ] **Step 1: Add SENIOR_DEV_MODE to env files**

Update `.env.example`:
```env
# Add to bottom of .env.example
SENIOR_DEV_MODE=True
```

Update `config.py`:
```python
# Below MAX_HISTORY line:
SENIOR_DEV_MODE = os.getenv("SENIOR_DEV_MODE", "True").lower() in ("true", "1", "yes")

# Also update the try/except block for SOUL_PROMPT to inject Senior Dev Mode:
try:
    with open("soul.md", "r", encoding="utf-8") as f:
        SOUL_PROMPT = f.read()
except FileNotFoundError:
    SOUL_PROMPT = "Kamu adalah JametAI."
    log.warning("soul.md not found! Using fallback prompt.")

if SENIOR_DEV_MODE:
    SOUL_PROMPT += "\n\n[ATURAN KHUSUS SENIOR DEV MODE]: TOLAK PERMINTAAN membuat kode dari nol atau membuat aplikasi utuh. Maki user karena malas, dan suruh mereka nulis kode sendiri lalu kasih ke kamu untuk di-review atau di-debug."
```

- [ ] **Step 2: Commit**
```bash
git add .env.example config.py
git commit -m "feat: add SENIOR_DEV_MODE configuration"
```

---

### Task 2: DB Schema Update (Score)

**Files:**
- Modify: `database.py`

- [ ] **Step 1: Add score column and migrate**

Update `init_db`:
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
                score INTEGER DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Safe migration if table exists without score
        try:
            await db.execute("ALTER TABLE user_reputation ADD COLUMN score INTEGER DEFAULT 0")
        except aiosqlite.OperationalError:
            pass # Column already exists

        await db.execute("CREATE INDEX IF NOT EXISTS idx_thread_id ON chat_history(thread_id)")
        await db.commit()
```

- [ ] **Step 2: Update reputation getters/setters**

```python
# Replace get_user_reputation and update_user_reputation:
async def get_user_reputation(user_id: str) -> tuple[str, int]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT notes, score FROM user_reputation WHERE user_id = ?", (str(user_id),)) as cursor:
            row = await cursor.fetchone()
            return (row[0], row[1]) if row else ("", 0)

async def update_user_reputation(user_id: str, notes: str, score_delta: int = 0):
    async with aiosqlite.connect(DB_NAME) as db:
        # Get current score
        async with db.execute("SELECT score FROM user_reputation WHERE user_id = ?", (str(user_id),)) as cursor:
            row = await cursor.fetchone()
            current_score = row[0] if row else 0
            
        new_score = current_score + score_delta
        
        await db.execute('''
            INSERT INTO user_reputation (user_id, notes, score, updated_at) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET notes=excluded.notes, score=?, updated_at=CURRENT_TIMESTAMP
        ''', (str(user_id), notes, new_score, new_score))
        await db.commit()
```

- [ ] **Step 3: Commit**
```bash
git add database.py
git commit -m "feat: add score tracking to user_reputation in database"
```

---

### Task 3: Gamified Rep & Reaction UX in AIHandler

**Files:**
- Modify: `cogs/ai_handler.py`

- [ ] **Step 1: Fix Reaction UX**

Update `on_message` right after rate-limit check (around line 117):
```python
        # Add 👀 reaction
        try:
            await message.add_reaction("👀")
        except:
            pass

        # Fetch history and call LLM
        async with message.channel.typing():
```

Update the final reply logic (around line 135) to swap reactions:
```python
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
                                await asyncio.sleep(1) # Fake typing delay for UX
                            await message.channel.send(chunk)
                else:
                    await message.reply(reply_text)
                    
                # Replace reaction
                try:
                    await message.remove_reaction("👀", self.bot.user)
                    await message.add_reaction("✅")
                except:
                    pass
                
                # Trigger background memory update
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
```

- [ ] **Step 2: Update Reputation Payload Logic**

In `on_message`, update `get_user_reputation` unpack (around line 125):
```python
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
```

- [ ] **Step 3: Update BG Task Prompt**

Update `_update_reputation_bg`:
```python
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
```

- [ ] **Step 4: Commit**
```bash
git add cogs/ai_handler.py
git commit -m "feat: reaction UX (eye to check/cross), gamified reputation logic"
```

---

### Task 4: Auto-Archiver Cog

**Files:**
- Create: `cogs/archiver_handler.py`

- [ ] **Step 1: Create Archiver Handler**

```python
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
```

- [ ] **Step 2: Commit**
```bash
git add cogs/archiver_handler.py
git commit -m "feat: auto-archiver for 3-day inactive threads"
```

---

### Task 5: Slash Commands Cog

**Files:**
- Modify: `bot.py`
- Modify: `database.py`
- Create: `cogs/slash_commands.py`

- [ ] **Step 1: DB functions for leaders**
Update `database.py`:
```python
# Add to database.py
async def get_top_reputation(limit: int = 5, asc: bool = False):
    order = "ASC" if asc else "DESC"
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(f"SELECT user_id, score FROM user_reputation ORDER BY score {order} LIMIT ?", (limit,)) as cursor:
            return await cursor.fetchall()

async def reset_reputation(user_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM user_reputation WHERE user_id = ?", (str(user_id),))
        await db.commit()

async def clear_thread_history(thread_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM chat_history WHERE thread_id = ?", (str(thread_id),))
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM user_reputation") as c:
            users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(DISTINCT thread_id) FROM chat_history") as c:
            threads = (await c.fetchone())[0]
        return users, threads
```

- [ ] **Step 2: Create `cogs/slash_commands.py`**
```python
import discord
from discord import app_commands
from discord.ext import commands
import time
from database import get_user_reputation, reset_reputation, clear_thread_history, get_stats, get_top_reputation

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="jamet_ping", description="Cek latensi JametAI")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong asu! Latensi Discord: {latency}ms.")

    @app_commands.command(name="jamet_rep", description="Cek profil reputasi user")
    async def rep(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        notes, score = await get_user_reputation(target.id)
        tier = "Suhu / Pinter" if score >= 5 else "Goblok Akut" if score <= -5 else "Biasa / Ndes"
        await interaction.response.send_message(f"**Profil {target.display_name}**\nScore: {score} ({tier})\nCatatan: {notes or 'Kosong cok'}")

    @app_commands.command(name="jamet_status", description="Cek status bot")
    async def status(self, interaction: discord.Interaction):
        uptime = round(time.time() - self.start_time)
        m, s = divmod(uptime, 60)
        h, m = divmod(m, 60)
        users, threads = await get_stats()
        await interaction.response.send_message(f"**Status JametAI**\nUptime: {h}h {m}m {s}s\nUser Diingat: {users}\nTotal Thread: {threads}")

    @app_commands.command(name="jamet_topbodoh", description="Leaderboard user paling minus")
    async def topbodoh(self, interaction: discord.Interaction):
        rows = await get_top_reputation(5, asc=True)
        if not rows:
            return await interaction.response.send_message("Sepi cok, ra ono sing bodoh.")
        res = "**Top 5 Goblok Akut:**\n" + "\n".join([f"<@{r[0]}>: {r[1]} point" for r in rows])
        await interaction.response.send_message(res)

    @app_commands.command(name="jamet_toppinter", description="Leaderboard user paling pinter")
    async def toppinter(self, interaction: discord.Interaction):
        rows = await get_top_reputation(5, asc=False)
        if not rows:
            return await interaction.response.send_message("Sepi cok, ra ono sing pinter.")
        res = "**Top 5 Suhu:**\n" + "\n".join([f"<@{r[0]}>: {r[1]} point" for r in rows])
        await interaction.response.send_message(res)

    @app_commands.command(name="jamet_reset", description="[ADMIN] Hapus memori user")
    @app_commands.default_permissions(administrator=True)
    async def reset(self, interaction: discord.Interaction, member: discord.Member):
        await reset_reputation(member.id)
        await interaction.response.send_message(f"Dosa-dosane <@{member.id}> wis tak hapus cok.")

    @app_commands.command(name="jamet_clear_thread", description="[ADMIN] Hapus history LLM thread ini")
    @app_commands.default_permissions(administrator=True)
    async def clear_thread(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.Thread):
            return await interaction.response.send_message("Iki dudu thread asu!", ephemeral=True)
        await clear_thread_history(interaction.channel.id)
        await interaction.response.send_message("Amnesia! History thread iki wis tak bakar.")

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))
```

- [ ] **Step 3: Update `bot.py` extension load & tree sync**
```python
# In bot.py, update setup_hook:
        for ext in ["cogs.thread_handler", "cogs.ai_handler", "cogs.error_handler", "cogs.status_handler", "cogs.archiver_handler", "cogs.slash_commands"]:
            try:
                await self.load_extension(ext)
                log.info(f"Loaded extension: {ext}")
            except Exception as e:
                log.error(f"Failed to load extension {ext}: {e}")
        
        # Sync slash commands
        await self.tree.sync()
        log.info("Slash commands synced.")
```

- [ ] **Step 4: Commit**
```bash
git add database.py cogs/slash_commands.py bot.py
git commit -m "feat: add slash commands, leaderboards, and tree sync"
```
