import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect(
        host='localhost', port=5433,
        user='postgres', password='postgres',
        database='codereview'
    )
    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname='public';"
    )
    print('Tables created:')
    for t in tables:
        print(' ✅', t['tablename'])
    await conn.close()

asyncio.run(check())