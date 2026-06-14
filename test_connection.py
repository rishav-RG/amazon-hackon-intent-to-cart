import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            user='postgres',
            password='password',
            database='intent_to_cart',
            host='localhost',
            port=5432
        )
        print("✓ Connection successful!")
        
        # Test query
        result = await conn.fetchval('SELECT COUNT(*) FROM intents')
        print(f"✓ Query successful! Intents count: {result}")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == '__main__':
    asyncio.run(test_connection())
