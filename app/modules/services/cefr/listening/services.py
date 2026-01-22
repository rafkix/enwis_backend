from typing import Dict, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from .models import (
    ListeningExam, 
    ListeningPart, 
    ListeningQuestion, 
    ListeningQuestionOption, 
    ListeningPartOption,
    ListeningResult
)
from .schemas import ListeningExamCreate, ListeningExamUpdate

def calculate_standard_score(correct_answers: int) -> int:
    """Agentlik shkalasi bo'yicha ballni hisoblash."""
    if 28 <= correct_answers <= 35:
        return 65 + (correct_answers - 28) * (75 - 65) // (35 - 28)
    elif 18 <= correct_answers <= 27:
        return 51 + (correct_answers - 18) * (64 - 51) // (27 - 18)
    elif 10 <= correct_answers <= 17:
        return 38 + (correct_answers - 10) * (50 - 38) // (17 - 10)
    else:
        return (correct_answers * 37) // 9 if correct_answers > 0 else 0

def get_cefr_level(std_score: float) -> str:
    if std_score >= 65: return "C1"
    if std_score >= 51: return "B2"
    if std_score >= 38: return "B1"
    return "A2 or below"

class ListeningService:
    def __init__(self, db):
        self.db = db
        
    async def create_exam(self, data: ListeningExamCreate):
        exists = await self.db.scalar(
            select(ListeningExam).where(ListeningExam.id == data.id)
        )
        if exists:
            raise HTTPException(400, "Listening exam already exists")

        exam = ListeningExam(**data.model_dump(exclude={"parts"}))
        self.db.add(exam)
        await self.db.flush()

        for part_data in data.parts:
            part = ListeningPart(
                exam_id=exam.id,
                **part_data.model_dump(exclude={"questions", "options"})
            )
            self.db.add(part)
            await self.db.flush()

            for opt in part_data.options:
                self.db.add(ListeningPartOption(part_id=part.id, **opt.model_dump()))

            for q_data in part_data.questions:
                question = ListeningQuestion(
                    part_id=part.id,
                    **q_data.model_dump(exclude={"options"})
                )
                self.db.add(question)
                await self.db.flush()

                for opt in q_data.options:
                    self.db.add(
                        ListeningQuestionOption(
                            question_id=question.id,
                            **opt.model_dump()
                        )
                    )

        await self.db.commit()
        await self.db.refresh(exam)
        return exam

    async def get_all_exams(self):
        stmt = (
            select(ListeningExam)
            .options(
                selectinload(ListeningExam.parts).options(
                    selectinload(ListeningPart.questions).selectinload(ListeningQuestion.options),
                    selectinload(ListeningPart.options)
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()

    async def get_exam_by_id(self, exam_id: str):
        stmt = (
            select(ListeningExam)
            .where(ListeningExam.id == exam_id)
            .options(
                selectinload(ListeningExam.parts).options(
                    selectinload(ListeningPart.questions).selectinload(ListeningQuestion.options),
                    selectinload(ListeningPart.options)
                )
            )
        )
        result = await self.db.execute(stmt)
        exam = result.unique().scalar_one_or_none()
        if not exam:
            raise HTTPException(status_code=404, detail="Listening Test not found")
        return exam

    async def submit_exam_and_get_result(self, user_id: int, exam_id: str, user_answers: Dict[str, str]):
        # 1. Imtihonni olish
        exam = await self.get_exam_by_id(exam_id)
        
        correct_count = 0
        total_q = 0
        
        # 2. Tekshirish logikasi
        for part in exam.parts:
            for q in part.questions:
                total_q += 1
                # Frontenddan kelgan javobni olish
                u_ans = user_answers.get(str(q.id), "").strip().lower()
                c_ans = q.correct_answer.strip().lower()
                
                if u_ans == c_ans:
                    correct_count += 1

        # 3. Hisoblashlar
        std_score = calculate_standard_score(correct_count)
        cefr_level = get_cefr_level(std_score)

        # 4. Bazaga saqlash (XATOLAR TUZATILDI)
        # Diqqat: ListeningResult modelida ustunlar nomini aniq tekshiring!
        new_result = ListeningResult(
            user_id=user_id,
            exam_id=exam_id,
            total_questions=total_q,        # correct_answers/total_questions deb nomlangani ma'qul
            correct_answers=correct_count,
            standard_score=std_score,
            cefr_level=cefr_level,
            user_answers=user_answers       # JSON formatda saqlanadi
        )
        
        self.db.add(new_result)
        await self.db.commit()
        await self.db.refresh(new_result)
        
        return {
            "summary": new_result,
            "correct_answers": correct_count,
            "total_questions": total_q,
            "standard_score": std_score,
            "cefr_level": cefr_level
        }

    async def get_user_results(self, user_id: int):
        stmt = (
            select(ListeningResult)
            .where(ListeningResult.user_id == user_id)
            .order_by(ListeningResult.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_result_details(self, result_id: int, user_id: int):
        stmt = select(ListeningResult).where(
            ListeningResult.id == result_id, 
            ListeningResult.user_id == user_id
        )
        res = await self.db.execute(stmt)
        result_data = res.scalar_one_or_none()
        
        if not result_data:
            raise HTTPException(status_code=404, detail="Natija topilmadi")

        exam = await self.get_exam_by_id(result_data.exam_id)
        
        review_data = []
        for part in exam.parts:
            for q in part.questions:
                u_ans = result_data.user_answers.get(str(q.id), "")
                review_data.append({
                    "question_number": q.question_number,
                    "user_answer": u_ans,
                    "correct_answer": q.correct_answer,
                    "is_correct": u_ans.strip().lower() == q.correct_answer.strip().lower()
                })
                
        return {
            "summary": result_data,
            "review": review_data
        }