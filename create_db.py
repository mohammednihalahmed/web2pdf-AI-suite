# scripts/create_tables.py
import asyncio
from services.database import init_db

asyncio.run(init_db())
print("✅ Tables created")


