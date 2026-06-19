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
            return [{"role": row[0], "content": row[1]} for row in reversed(rows)]
