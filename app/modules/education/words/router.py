from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, String

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from .models import (
    Word,
    WordCategory,
    WordCategoryItem,
    WordExample,
    WordSynonym,
    UserWord,
    UserWordHistory,
)
from .schemas import (
    WordCreate,
    WordOut,
    WordUpdate,
    WordCategoryCreate,
    WordCategoryOut,
    WordCategoryUpdate,
    UserWordAdd,
    UserWordOut,
    ReviewAttempt,
)

router = APIRouter(prefix="/words", tags=["Words"])

ADMIN_ROLES = {"admin", "teacher", "mentor"}


def sm2_update(user_word: UserWord, quality: int) -> dict:
    ef = float(user_word.efactor or 2.5) # type: ignore
    reps = int(user_word.repetitions or 0) # type: ignore
    interval = int(user_word.interval_days or 0) # type: ignore

    if quality < 3:
        reps = 0
        interval = 1
    else:
        reps += 1
        if reps == 1:
            interval = 1
        elif reps == 2:
            interval = 6
        else:
            interval = int(round(interval * ef))

    ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ef = max(ef, 1.3)

    return {
        "efactor": ef,
        "interval_days": interval,
        "repetitions": reps,
        "next_review_at": datetime.utcnow() + timedelta(days=interval),
        "stage": (
            "MASTERED" if reps >= 10
            else "REVIEW" if reps >= 3
            else "LEARNING" if reps >= 1
            else "NEW"
        ),
    }


@router.get("/categories/all", response_model=List[WordCategoryOut])
async def list_categories(
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WordCategory)
    if q:
        stmt = stmt.where(WordCategory.title.ilike(f"%{q}%"))
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/all", response_model=list[WordOut])
async def get_all_words(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Word))
    return result.scalars().all()


@router.get("/search", response_model=List[WordOut])
async def search_words(
    q: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Word).order_by(Word.id.desc()).limit(limit).offset(offset)
    if q:
        ilike = f"%{q}%"
        stmt = select(Word).where(
            or_(
                Word.lemma.ilike(ilike),
                Word.meaning.ilike(ilike),
                func.cast(Word.tags, String).ilike(ilike),
            )
        )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/select/{word_id}", response_model=WordOut)
async def get_word(word_id: int, db: AsyncSession = Depends(get_db)):
    word = await db.scalar(select(Word).where(Word.id == word_id))
    if not word:
        raise HTTPException(404, "Word not found")
    return word

@router.get("/user", response_model=List[UserWordOut])
async def list_user_words(
    due_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(UserWord).where(UserWord.user_id == current_user.id)
    if due_only:
        stmt = stmt.where(UserWord.next_review_at <= datetime.utcnow())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/user/{user_word_id}/review")
async def review_word(
    user_word_id: int,
    payload: ReviewAttempt,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uw = await db.scalar(select(UserWord).where(UserWord.id == user_word_id))
    if not uw or uw.user_id != current_user.id: # type: ignore
        raise HTTPException(404, "Not found")

    upd = sm2_update(uw, payload.quality)

    uw.efactor = upd["efactor"]
    uw.interval_days = upd["interval_days"]
    uw.repetitions = upd["repetitions"]
    uw.next_review_at = upd["next_review_at"]
    uw.last_reviewed_at = datetime.utcnow() # type: ignore
    uw.stage = upd["stage"]

    db.add(
        UserWordHistory(
            user_word_id=uw.id,
            outcome="correct" if payload.quality >= 3 else "wrong",
            response={"quality": payload.quality},
            points=1 if payload.quality >= 3 else 0,
        )
    )

    await db.commit()
    return {"next_review_at": uw.next_review_at, "stage": uw.stage}


@router.post("/categories/create", response_model=WordCategoryOut, status_code=201)
async def create_category(
    data: WordCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    exists = await db.scalar(
        select(WordCategory.id).where(func.lower(WordCategory.title) == data.title.lower())
    )
    if exists:
        raise HTTPException(400, "Category already exists")

    category = WordCategory(**data.dict())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category

@router.post("/create", response_model=WordOut, status_code=201)
async def create_word(
    payload: WordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    word = Word(
        lemma=payload.lemma,
        pos=payload.pos,
        base_language=payload.base_language or "en",
        meaning=payload.meaning,
        transcription=payload.transcription,
        difficulty=payload.difficulty,
        tags=payload.tags,
        meta_data=payload.meta_data,
        example_count=len(payload.examples or []),
    )

    db.add(word)
    await db.flush()

    if payload.examples:
        for ex in payload.examples:
            db.add(
                WordExample(
                    word_id=word.id,
                    text=ex.text,
                    translation=ex.translation,
                    source=ex.source,
                    is_preferred=ex.is_preferred,
                )
            )

    if payload.synonyms:
        for s in payload.synonyms:
            db.add(WordSynonym(word_id=word.id, synonym=s.synonym, type=s.type))

    if payload.categories: # type: ignore
        for cat_id in payload.categories: # type: ignore
            exists = await db.scalar(
                select(WordCategory.id).where(WordCategory.id == cat_id)
            )
            if not exists:
                raise HTTPException(404, f"Category {cat_id} not found")
            db.add(WordCategoryItem(word_id=word.id, category_id=cat_id))

    await db.commit()
    await db.refresh(word)
    return word

@router.post("/user/add_word", response_model=UserWordOut, status_code=201)
async def add_user_word(
    payload: UserWordAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exists = await db.scalar(
        select(UserWord.id).where(
            UserWord.user_id == current_user.id,
            UserWord.word_id == payload.word_id,
        )
    )
    if exists:
        raise HTTPException(400, "Word already added")

    uw = UserWord(user_id=current_user.id, word_id=payload.word_id)
    db.add(uw)
    await db.commit()
    await db.refresh(uw)
    return uw


@router.patch("/categories/select/{category_id}", response_model=WordCategoryOut)
async def update_category(
    category_id: int,
    data: WordCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    category = await db.scalar(select(WordCategory).where(WordCategory.id == category_id))
    if not category:
        raise HTTPException(404, "Category not found")

    for k, v in data.dict(exclude_unset=True).items():
        setattr(category, k, v)

    await db.commit()
    await db.refresh(category)
    return category


@router.patch("/update/{word_id}", response_model=WordOut)
async def update_word(
    word_id: int,
    data: WordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    word = await db.scalar(select(Word).where(Word.id == word_id))
    if not word:
        raise HTTPException(404, "Word not found")

    for k, v in data.dict(exclude_unset=True).items():
        setattr(word, k, v)

    await db.commit()
    await db.refresh(word)
    return word
