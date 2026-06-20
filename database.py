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
            return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

async def prune_history(thread_id: str, keep_limit: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            DELETE FROM chat_history 
            WHERE thread_id = ? AND id NOT IN (
                SELECT id FROM chat_history 
                WHERE thread_id = ? 
                ORDER BY id DESC LIMIT ?
            )
        ''', (str(thread_id), str(thread_id), keep_limit))
        await db.commit()

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
