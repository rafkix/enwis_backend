from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.database import get_db as get_async_session
from app.models.daily_vocab_model import DailyVocabWords
from app.schemas.daily_vocab import (
    DailyVocabCreate,
    DailyVocabUpdate,
    DailyVocabResponse,
    DictionaryResponse,
    Definition,
)

router = APIRouter(prefix="/daily-words", tags=["Daily Vocabulary"])

DICT_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"


async def fetch_dictionary(word: str) -> DictionaryResponse | None:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get(f"{DICT_URL}/{word}")

        if res.status_code != 200:
            return None

        entry = res.json()[0]

        phonetic = (
            entry.get("phonetic")
            or next(
                (p.get("text") for p in entry.get("phonetics", []) if p.get("text")), 
                None
            )
        )

        audio = next(
            (p.get("audio") for p in entry.get("phonetics", []) if p.get("audio")), 
            None
        )

        meanings = entry.get("meanings", [])

        definitions: list[Definition] = []
        synonyms: set[str] = set()
        antonyms: set[str] = set()

        for m in meanings:
            for d in m.get("definitions", []):
                definitions.append(
                    Definition(
                        definition=d["definition"],
                        example=d.get("example"),
                    )
                )
            synonyms.update(m.get("synonyms", []))
            antonyms.update(m.get("antonyms", []))

        return DictionaryResponse(
            word=word,
            phonetic=phonetic,
            part=meanings[0].get("partOfSpeech") if meanings else None,
            audio=audio,
            definitions=definitions,
            synonyms=list(synonyms),
            antonyms=list(antonyms),
            origin=entry.get("origin"),
        )

    except Exception:
        return None

@router.get(
    "",
    response_model=list[DailyVocabResponse],
)
async def get_daily_words(
    session: AsyncSession = Depends(get_async_session),  # noqa: F821
):
    result = await session.execute(
        select(DailyVocabWords).order_by(DailyVocabWords.created_at.desc())
    )
    return result.scalars().all()

@router.get(
    "/select/{word}",
)
async def get_word_details(
    word: str,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(DailyVocabWords).where(DailyVocabWords.word.ilike(word))
    )
    db_word = result.scalar_one_or_none()

    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")

    dictionary = await fetch_dictionary(db_word.word) # type: ignore

    return {
        "id": db_word.id,
        "word": db_word.word,
        "level": db_word.level,
        "uzTranslate": db_word.uzTranslate,
        "dictionary": dictionary,
    }

@router.post(
    "/create_word",
    response_model=DailyVocabResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_word(
    data: DailyVocabCreate,
    session: AsyncSession = Depends(get_async_session),
):
    exists = await session.execute(
        select(DailyVocabWords).where(DailyVocabWords.word == data.word)
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Word already exists")

    word = DailyVocabWords(**data.model_dump())
    session.add(word)
    await session.commit()
    await session.refresh(word)

    return word

@router.patch(
    "/update_word/{word_id}",
    response_model=DailyVocabResponse,
)
async def update_word(
    word_id: int,
    data: DailyVocabUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    word = await session.get(DailyVocabWords, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(word, key, value)

    await session.commit()
    await session.refresh(word)

    return word

@router.delete(
    "/{word_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_word(
    word_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    word = await session.get(DailyVocabWords, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    await session.delete(word)
    await session.commit()
