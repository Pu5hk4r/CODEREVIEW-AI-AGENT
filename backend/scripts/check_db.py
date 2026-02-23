import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect(
        host='localhost', port=5433,
        user='postgres', password='postgres',
        database='codereview'
    )
    
    # Check tables
    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname='public';"
    )
    print('Tables:')
    for t in tables:
        print(' ✅', t['tablename'])
    
    # Check reviews
    reviews = await conn.fetch("SELECT * FROM reviews;")
    print(f'\nReviews in DB: {len(reviews)}')
    for r in reviews:
        print(f'  PR #{r["pr_number"]} — {r["pr_title"]} | approved={r["approved"]}')
    
    await conn.close()

asyncio.run(check())