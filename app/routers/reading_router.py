from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reading_model import (
    ReadingTest,
    ReadingPart,
    ReadingQuestion,
    ReadingAttempt,
    ReadingUserAnswer,
)

from app.schemas.reading_schema import (
    ReadingTestCreate,
    ReadingTestRead,
    ReadingTestPublic,
    ReadingSubmitSchema,
    ReadingResultSchema,
)

router = APIRouter(prefix="/reading", tags=["Reading"])


@router.get(
    "/get/reading-test",
    response_model=list[ReadingTestPublic]
)
async def get_reading_tests(
    db: AsyncSession = Depends(get_db) # type: ignore
):
    stmt = (
        select(ReadingTest)
        .options(
            selectinload(ReadingTest.parts)
            .selectinload(ReadingPart.questions)
        )
        .where(ReadingTest.is_active)
    )

    result = await db.execute(stmt)
    tests = result.scalars().unique().all()

    return tests


@router.get("/exams/get_{test_id}", response_model=ReadingTestPublic)
def get_reading_test(test_id: int, db: Session = Depends(get_db)):  # noqa: F821
    test = db.query(ReadingTest).filter_by(id=test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Reading test not found")
    return test

@router.post("/exams/create-reading", response_model=ReadingTestRead)
async def create_reading_test(
    data: ReadingTestCreate,
    db: Session = Depends(get_db),
):
    test = ReadingTest(**data.dict(exclude={"parts"}))
    db.add(test)
    await db.flush() # type: ignore

    for part_data in data.parts:
        part = ReadingPart(
            test_id=test.id,
            **part_data.dict(exclude={"questions"})
        )
        db.add(part)
        await db.flush() # type: ignore

        for q in part_data.questions:
            db.add(
                ReadingQuestion(
                    part_id=part.id,
                    **q.dict()
                )
            )

    await db.commit() # type: ignore

    # 🔥 MUHIM QATOR
    result = await db.execute(
        select(ReadingTest)
        .options(
            selectinload(ReadingTest.parts)
            .selectinload(ReadingPart.questions)
        )
        .where(ReadingTest.id == test.id)
    ) # type: ignore
    test = result.scalar_one()

    return test



@router.post("/exam/submit", response_model=ReadingResultSchema)
def submit_reading_answers(
    payload: ReadingSubmitSchema,
    db: Session = Depends(get_db),
    user_id: int = 1,  # authdan olinadi
):
    test = db.query(ReadingTest).filter_by(id=payload.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    attempt = ReadingAttempt(user_id=user_id, test_id=test.id)
    db.add(attempt)
    db.flush()

    correct = 0

    for item in payload.answers:
        question = db.query(ReadingQuestion).filter_by(id=item.question_id).first()
        if not question:
            continue

        is_correct = item.answer == question.correct_answer
        if is_correct:
            correct += 1

        db.add(
            ReadingUserAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                user_answer=item.answer,
                is_correct=is_correct,
            )
        )

    attempt.score = correct # type: ignore
    db.commit()

    return ReadingResultSchema(
        test_id=test.id, # type: ignore
        total_questions=len(payload.answers),
        correct_answers=correct,
        score=correct,
        band_score=None,
    )

@router.get("/exam/resualt/{test_id}", response_model=ReadingResultSchema)
def get_reading_result(
    test_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1,
):
    attempt = (
        db.query(ReadingAttempt)
        .filter_by(test_id=test_id, user_id=user_id)
        .order_by(ReadingAttempt.id.desc())
        .first()
    )

    if not attempt:
        raise HTTPException(status_code=404, detail="Result not found")

    return ReadingResultSchema(
        test_id=test_id,
        total_questions=attempt.score, # type: ignore
        correct_answers=attempt.score, # type: ignore
        score=attempt.score, # type: ignore
        band_score=None,
    )

