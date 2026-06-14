"""Test Neon database connection and create tables."""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Extract connection parameters from the URL
# postgresql+asyncpg://user:password@host/database?sslmode=require
url = DATABASE_URL.replace("postgresql+asyncpg://", "")
parts = url.split("@")
user_pass = parts[0].split(":")
host_db = parts[1].split("/")
host = host_db[0]
db_params = host_db[1].split("?")
database = db_params[0]

user = user_pass[0]
password = user_pass[1]

print(f"Connecting to Neon database...")
print(f"Host: {host}")
print(f"Database: {database}")
print(f"User: {user}")

async def test_connection():
    try:
        # Connect to the database
        conn = await asyncpg.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            ssl='require'
        )
        
        print("✅ Connection successful!")
        
        # Test query
        result = await conn.fetchval('SELECT 1')
        print(f"✅ Test query successful: {result}")
        
        # Check if tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        if tables:
            print(f"\n📋 Existing tables:")
            for table in tables:
                print(f"  - {table['table_name']}")
        else:
            print("\n⚠️  No tables found in database")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    if success:
        print("\n🎉 Database is ready to use!")
    else:
        print("\n❌ Please check your database credentials")
