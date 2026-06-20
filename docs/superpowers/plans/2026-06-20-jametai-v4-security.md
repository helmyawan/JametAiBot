# JametAI V4 Security Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement anti-prompt injection, attachment token bombing protection, and slash command rate-limiting for JametAI.

**Architecture:** Modifies `cogs/ai_handler.py` to add regex heuristics and character limits for attachments. Modifies `cogs/slash_commands.py` to add cooldown decorators and error handlers for app commands.

**Tech Stack:** Python 3.11+, discord.py, re

---

### Task 1: Attachment Token Bombing Protection

**Files:**
- Modify: `cogs/ai_handler.py`

- [ ] **Step 1: Truncate attachment text to 8000 chars**

In `cogs/ai_handler.py`, update `process_attachments`:
```python
            try:
                content = await att.read()
                text_content = content.decode('utf-8')
                
                # Truncate if too long (Token Bombing Protection)
                if len(text_content) > 8000:
                    text_content = text_content[:8000] + "\n\n...[TRUNCATED: Kepanjangan cok! Kodingan opo bacotan iki?]"
                    
                file_contents.append(f"\n\n--- Isi File: {att.filename} ---\n{text_content}\n--- End File ---")
            except Exception as e:
```

- [ ] **Step 2: Commit changes**
```bash
git add cogs/ai_handler.py
git commit -m "feat: truncate attachment text to 8000 chars to prevent token bombing"
```

---

### Task 2: Anti-Prompt Injection

**Files:**
- Modify: `cogs/ai_handler.py`

- [ ] **Step 1: Add jailbreak heuristics and ban logic**

In `cogs/ai_handler.py`, add the regex at the top level:
```python
JAILBREAK_KEYWORDS = re.compile(
    r'(ignore all previous|you are now|forget your persona|disregard the previous|system prompt|bypass instructions)', 
    re.IGNORECASE
)
```

Update `on_message` right after fetching `final_user_content` and before `get_history`:
```python
        # Fetch file content if any
        attachment_text = await self.process_attachments(message)
        final_user_content = message.content + attachment_text

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
```

- [ ] **Step 2: Commit changes**
```bash
git add cogs/ai_handler.py
git commit -m "feat: add anti-prompt injection heuristics and auto-ban logic"
```

---

### Task 3: Slash Command Rate-Limiter

**Files:**
- Modify: `cogs/slash_commands.py`

- [ ] **Step 1: Add cooldowns and error handler**

In `cogs/slash_commands.py`, add imports and update the cog:
```python
import discord
from discord import app_commands
from discord.ext import commands
import time
import math
from database import get_user_reputation, reset_reputation, clear_thread_history, get_stats, get_top_reputation

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            wait_time = math.ceil(error.retry_after)
            await interaction.response.send_message(f"Kesuwen asu! Ngenteni {wait_time} detik maneh cok.", ephemeral=True)
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("Raimu sopo cok? Kowe dudu admin!", ephemeral=True)
        else:
            await interaction.response.send_message("Error bajilak! Gak iso ngeksekusi command.", ephemeral=True)

    @app_commands.command(name="jamet_ping", description="Cek latensi JametAI")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def ping(self, interaction: discord.Interaction):
```
(Apply `@app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)` to ALL commands: ping, rep, status, topbodoh, toppinter, reset, clear_thread).

- [ ] **Step 2: Commit changes**
```bash
git add cogs/slash_commands.py
git commit -m "feat: add 10s cooldown rate-limiter to all slash commands"
```
