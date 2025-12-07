from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import (
    Word, WordExample, WordAudio, WordSynonym,
    WordCategory, WordCategoryItem
)
from app.schemas.words_schema import WordCreate
from app.utils.services.audio_provider import AudioProviderService


class WordService:

    @staticmethod
    async def create_word(db: AsyncSession, data: WordCreate):

        # main word
        word = Word(
            lemma=data.lemma,
            pos=data.pos,
            base_language=data.base_language or "en",
            meaning=data.meaning,
            transcription=data.transcription,
            difficulty=data.difficulty,
            tags=data.tags,
            meta_data=data.meta_data,
            example_count=len(data.examples or [])
        )

        db.add(word)
        await db.flush()  # get word.id

        # --- Examples ---
        if data.examples:
            for e in data.examples:
                db.add(WordExample(
                    word_id=word.id,
                    text=e.text,
                    translation=e.translation,
                    source=e.source,
                    is_preferred=e.is_preferred
                ))

        # --- Synonyms ---
        if data.synonyms:
            for s in data.synonyms:
                db.add(WordSynonym(
                    word_id=word.id,
                    synonym=s.synonym,
                    type=s.type
                ))

        # --- Categories ---
        if data.categories:
            for cat_id in data.categories:
                res = await db.execute(select(WordCategory).where(WordCategory.id == cat_id))
                cat = res.scalars().first()
                if not cat:
                    raise HTTPException(404, f"Category {cat_id} not found")
                db.add(WordCategoryItem(word_id=word.id, category_id=cat_id))

        # --- Automatic TTS (ElevenLabs) ---
        audio_data = await AudioProviderService.generate_audio(text=data.lemma)

        db.add(WordAudio(
            word_id=word.id,
            provider="elevenlabs",
            url=audio_data["url"],
            duration=audio_data["duration"],
            meta_data=audio_data["meta_data"]
        ))

        return word
