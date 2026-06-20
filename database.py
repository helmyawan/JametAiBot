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
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
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
