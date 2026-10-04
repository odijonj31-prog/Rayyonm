from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Base
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Jadvallarni yaratadi va eski jadvallarga yangi ustunlarni qo'shadi (migratsiya)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        migrations = [
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS contact_name VARCHAR(255)",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(32)",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_date VARCHAR(32)",
            "ALTER TABLE portfolio_items ADD COLUMN IF NOT EXISTS category VARCHAR(64)",
        ]
        for sql in migrations:
            try:
                await conn.execute(text(sql))
            except Exception as e:
                print(f"⚠️ Migratsiya xatosi (e'tiborsiz qoldirildi): {e}")
