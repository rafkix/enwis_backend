import asyncio
from app.core.database import engine, Base

# DIQQAT: Barcha modellarni shu yerga import qilish SHART!
# Aks holda SQLAlchemy ularni ko'rmaydi va jadval yaratmaydi.
from app.modules.services.exams.reading.models import (
    ReadingTest, 
    ReadingPart, 
    ReadingQuestion, 
    ReadingOption, 
    ReadingResult
)

async def init_models():
    print("🔄 Jadvallar yaratilmoqda...")
    async with engine.begin() as conn:
        # Barcha jadvallarni yaratish
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Jadvallar muvaffaqiyatli yaratildi!")

if __name__ == "__main__":
    asyncio.run(init_models())