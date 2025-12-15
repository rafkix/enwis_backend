# app/routers/words_router.py
from __future__ import annotations
from typing import List, Optional
from datetime import datetime, timedelta

from aiosqlite import IntegrityError
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import String, or_, func

from app.database import get_db
from app.routers.auth_router import get_current_user
from app.models.words_model import (
    Word, WordCategoryItem, WordExample, WordAudio, WordSynonym,
    WordCategory, UserWord, UserWordHistory
)
from app.models.user_model import User
from app.schemas.words_schema import (
    WordCreate, WordOut, WordUpdate,
    WordCategoryCreate, WordCategoryOut, WordCategoryUpdate,
    UserWordAdd, UserWordOut, ReviewAttempt
)

router = APIRouter(prefix="/words", tags=["Words"])


# -----------------------
# Helper: SM-2 algorithm update
# -----------------------
def sm2_update(user_word: UserWord, quality: int) -> dict:
    """
    Update SRS params according to SM-2.
    quality: 0..5
    returns dict with new efactor, interval_days, repetitions, next_review_at, stage
    """
    # read existing
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

    # update efactor
    ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ef < 1.3:
        ef = 1.3

    next_review = datetime.utcnow() + timedelta(days=interval)

    # stage determination (simple)
    if reps >= 10:
        stage = "MASTERED"
    elif reps >= 3:
        stage = "REVIEW"
    elif reps >= 1:
        stage = "LEARNING"
    else:
        stage = "NEW"

    return {
        "efactor": ef,
        "interval_days": interval,
        "repetitions": reps,
        "next_review_at": next_review,
        "stage": stage
    }


# -----------------------
# Categories CRUD
# -----------------------
@router.post("/create_categories", response_model=WordCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(data: WordCategoryCreate, db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin", "mentor", "teacher"):
        raise HTTPException(status_code=403, detail="Forbidden")

    # check exists
    q = await db.execute(select(WordCategory).where(func.lower(WordCategory.title) == data.title.lower()))
    if q.scalars().first():
        raise HTTPException(status_code=400, detail="Category exists")

    cat = WordCategory(
        title=data.title,
        description=data.description,
        language=data.language,
        icon=data.icon,
        is_active=1 if data.is_active else 0
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.get("/get_categories", response_model=List[WordCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db), q: Optional[str] = Query(None)):
    stmt = select(WordCategory)
    if q:
        stmt = select(WordCategory).where(WordCategory.title.ilike(f"%{q}%"))
    res = await db.execute(stmt)
    return res.scalars().all()


@router.patch("/categories/{category_id}", response_model=WordCategoryOut)
async def update_category(category_id: int, data: WordCategoryUpdate,
                            db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin", "mentor", "teacher"):
        raise HTTPException(status_code=403, detail="Forbidden")

    res = await db.execute(select(WordCategory).where(WordCategory.id == category_id))
    cat = res.scalars().first()
    if not cat:
        raise HTTPException(404, "Category not found")

    for k, v in data.dict(exclude_unset=True).items():
        setattr(cat, k, v)
    await db.commit()
    await db.refresh(cat)
    return cat


# -----------------------
# Words CRUD + search
# -----------------------
@router.post("/create_word", response_model=WordOut, status_code=status.HTTP_201_CREATED)
async def create_word(
    payload: WordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Permissions
    if current_user.role not in ("admin", "teacher", "mentor", "student"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Create main word record
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
    try:
        # flush so word.id is available for related records
        await db.flush()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create word")

    # add examples
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

    # add audios
    if payload.audios:
        for a in payload.audios:
            db.add(
                WordAudio(
                    word_id=word.id,
                    provider=a.provider,
                    url=a.url,
                    duration=a.duration,
                    meta_data=a.meta_data,
                )
            )

    # add synonyms
    if payload.synonyms:
        for s in payload.synonyms:
            db.add(
                WordSynonym(
                    word_id=word.id,
                    synonym=s.synonym,
                    type=s.type,
                )
            )

    # link categories (optional)
    if getattr(payload, "categories", None):
        # validate categories exist and create pivot rows
        for cat_id in payload.categories: # type: ignore
            # ensure category exists
            res = await db.execute(select(WordCategory).where(WordCategory.id == cat_id))
            cat = res.scalars().first()
            if not cat:
                await db.rollback()
                raise HTTPException(status_code=404, detail=f"Category id {cat_id} not found")
            # avoid duplicate pivot if any unique constraint triggers
            db.add(WordCategoryItem(word_id=word.id, category_id=cat_id))

    # commit everything
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # likely duplicate unique constraint or FK issue
        raise HTTPException(status_code=400, detail="Integrity error while creating word")
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Unexpected error while creating word")

    # refresh to load relationships
    await db.refresh(word)
    return word


@router.get("/search", response_model=List[WordOut])
async def search_words(q: Optional[str] = Query(None), limit: int = 25, offset: int = 0,
                        db: AsyncSession = Depends(get_db)):
    stmt = select(Word).order_by(Word.id.desc()).limit(limit).offset(offset)
    if q:
        # search by lemma, meaning, tags
        ilike_q = f"%{q}%"
        stmt = select(Word).where(
            or_(
                Word.lemma.ilike(ilike_q),
                Word.meaning.ilike(ilike_q),
                func.cast(Word.tags, String).ilike(ilike_q)
            )
        ).order_by(Word.id.desc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/get_word/{word_id}", response_model=WordOut)
async def get_word(word_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Word).where(Word.id == word_id))
    w = res.scalars().first()
    if not w:
        raise HTTPException(status_code=404, detail="Word not found")
    return w


@router.patch("/update_word/{word_id}", response_model=WordOut)
async def update_word(word_id: int, data: WordUpdate, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin", "teacher", "mentor"):
        raise HTTPException(status_code=403, detail="Forbidden")
    res = await db.execute(select(Word).where(Word.id == word_id))
    w = res.scalars().first()
    if not w:
        raise HTTPException(404, "Not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(w, k, v)
    await db.commit()
    await db.refresh(w)
    return w


# -----------------------
# User words (SRS)
# -----------------------
@router.post("/user/add", response_model=UserWordOut, status_code=status.HTTP_201_CREATED)
async def add_user_word(payload: UserWordAdd, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    # ensure word exists
    res = await db.execute(select(Word).where(Word.id == payload.word_id))
    w = res.scalars().first()
    if not w:
        raise HTTPException(404, "Word not found")

    # avoid duplicates
    res = await db.execute(select(UserWord).where(UserWord.user_id == current_user.id,
                                                    UserWord.word_id == payload.word_id))
    existing = res.scalars().first()
    if existing:
        return existing

    uw = UserWord(user_id=current_user.id, word_id=payload.word_id)
    db.add(uw)
    await db.commit()
    await db.refresh(uw)
    return uw


@router.get("/user", response_model=List[UserWordOut])
async def list_user_words(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
                            due_only: bool = Query(False)):
    stmt = select(UserWord).where(UserWord.user_id == current_user.id)
    if due_only:
        stmt = stmt.where(UserWord.next_review_at <= datetime.utcnow())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/user/{user_word_id}/review", status_code=200)
async def review_user_word(user_word_id: int, payload: ReviewAttempt,
                            db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    # fetch user_word
    res = await db.execute(select(UserWord).where(UserWord.id == user_word_id))
    uw = res.scalars().first()
    if not uw or uw.user_id != current_user.id: # type: ignore
        raise HTTPException(404, "UserWord not found")

    # apply SM-2 update
    upd = sm2_update(uw, payload.quality)

    # persist
    uw.efactor = upd["efactor"]
    uw.interval_days = upd["interval_days"]
    uw.repetitions = upd["repetitions"]
    uw.next_review_at = upd["next_review_at"]
    uw.last_reviewed_at = datetime.utcnow() # type: ignore
    uw.streak = uw.streak + 1 if payload.quality >= 3 else 0 # type: ignore
    # update stage enum string or actual Enum depending on model
    try:
        uw.stage = upd["stage"]
    except Exception:
        # if stage is Enum instance expected, keep simple
        pass

    # history record
    hist = UserWordHistory(user_word_id=uw.id, outcome=("correct" if payload.quality >= 3 else "wrong"),
                            response={"quality": payload.quality}, points=(1 if payload.quality >= 3 else 0))
    db.add(hist)
    await db.commit()
    await db.refresh(uw)
    return {"status": "ok", "next_review_at": uw.next_review_at, "score": payload.quality}


# -----------------------
# Bulk import helper (simple)
# -----------------------
@router.post("/import/bulk", status_code=201)
async def bulk_import(words: List[WordCreate], db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin", "teacher", "mentor"):
        raise HTTPException(403, "Forbidden")
    created = []
    for w in words:
        word = Word(
            lemma=w.lemma,
            pos=w.pos,
            base_language=w.base_language,
            meaning=w.meaning,
            transcription=w.transcription,
            difficulty=w.difficulty,
            tags=w.tags,
            meta_data=w.meta_data,
            example_count=len(w.examples or [])
        )
        db.add(word)
        await db.flush()
        if w.examples:
            for ex in w.examples:
                db.add(WordExample(word_id=word.id, text=ex.text, translation=ex.translation,
                                    source=ex.source, is_preferred=ex.is_preferred))
        created.append(word)
    await db.commit()
    return {"created": len(created)}
