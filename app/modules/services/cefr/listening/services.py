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
        # 1. Asosiy imtihonni (Exam) yaratish
        new_exam = ListeningExam(
            id=data.id,
            title=data.title,
            is_demo=data.isDemo,
            is_free=data.isFree,
            sections=data.sections,
            level=data.level,
            duration=data.duration,
            total_questions=data.totalQuestions
        )
        self.db.add(new_exam)
        
        # 2. Part (Bo'limlarni) aylanish
        for p_data in data.parts:
            new_part = ListeningPart(
                exam_id=new_exam.id,
                part_number=p_data.partNumber,
                title=p_data.title,
                instruction=p_data.instruction,
                task_type=p_data.taskType,
                audio_label=p_data.audioLabel,
                context=p_data.context,
                passage=p_data.passage,
                map_image=p_data.mapImage
            )
            self.db.add(new_part)
            await self.db.flush() # Part ID sini olish uchun

            # 3. Part darajasidagi Optionlarni saqlash (Matching/Map uchun)
            if p_data.options:
                for opt in p_data.options:
                    new_p_opt = ListeningPartOption(
                        part_id=new_part.id,
                        value=opt.value,
                        label=opt.label
                    )
                    self.db.add(new_p_opt)

            # 4. Savollarni (Questions) aylanish
            for q_data in p_data.questions:
                new_question = ListeningQuestion(
                    part_id=new_part.id,
                    question_number=q_data.questionNumber,
                    type=q_data.type,
                    question=q_data.question,
                    correct_answer=q_data.correctAnswer
                )
                self.db.add(new_question)
                await self.db.flush() # Question ID sini olish uchun

                # 5. Savol darajasidagi Optionlarni saqlash (Multiple Choice bo'lsa)
                if q_data.options:
                    for opt in q_data.options:
                        new_q_opt = ListeningQuestionOption(
                            question_id=new_question.id,
                            value=opt.value,
                            label=opt.label
                        )
                        self.db.add(new_q_opt)

        # 6. Hammasini bittada commit qilish
        try:
            await self.db.commit()
            await self.db.refresh(new_exam)
            return await self.get_exam_by_id(new_exam.id)
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Imtihonni yaratishda xatolik: {str(e)}"
            )
        
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