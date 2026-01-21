from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict

# Modellarni va sxemalarni to'g'ri yo'ldan import qiling
from .models import (
    Exam, 
    ReadingPart, 
    Question, 
    QuestionOption, 
    ExamResult
)
from .schemas import ExamCreate, ResultSubmission, ExamUpdate

class ReadingExamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------------------
    # 1. CREATE: Imtihonni barcha qismlari bilan yaratish
    # ----------------------------------------------------------------
    async def create_exam(self, payload: ExamCreate):
        # Asosiy Exam ob'ektini yaratish
        exam = Exam(
            id=payload.id,
            title=payload.title,
            cefr_level=payload.cefr_level,
            duration_minutes=payload.duration_minutes,
            language=payload.language,
            type=payload.type,
            total_questions=payload.total_questions # <-- BU QATOR MUHIM (JSON dagi malumot uchun)
        )

        for p_data in payload.parts:
            part = ReadingPart(
                title=p_data.title,
                description=p_data.description,
                passage=p_data.passage
            )
            
            for q_idx, q_data in enumerate(p_data.questions):
                question = Question(
                    question_number=q_data.question_number or (q_idx + 1),
                    type=q_data.type,
                    text=q_data.text,
                    correct_answer=q_data.correct_answer,
                    word_limit=q_data.word_limit
                )
                
                if q_data.options:
                    for opt in q_data.options:
                        question.options.append(
                            QuestionOption(label=opt.label, value=opt.value)
                        )
                
                part.questions.append(question)
            
            exam.parts.append(part)

        self.db.add(exam)
        await self.db.commit()
        
        # MissingGreenlet xatosini oldini olish uchun hamma narsani yuklab qaytaramiz
        return await self.get_exam(exam.id)

    # ----------------------------------------------------------------
    # 2. GET: Imtihonni barcha relationship'lari bilan olish
    # ----------------------------------------------------------------
    async def get_exam(self, exam_id: str) -> Optional[Exam]:
        stmt = (
            select(Exam)
            .where(Exam.id == exam_id)
            .options(
                selectinload(Exam.parts)
                .selectinload(ReadingPart.questions)
                .selectinload(Question.options)
            )
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()
    
    # ----------------------------------------------------------------
    # 3. UPDATE: Mavjud imtihonni yangilash
    # ----------------------------------------------------------------
    async def update_exam(self, exam_id: str, data: ExamUpdate):
        exam = await self.get_exam(exam_id)
        if not exam: return None

        # Asosiy maydonlarni yangilash
        if data.title: exam.title = data.title
        if data.cefr_level: exam.cefr_level = data.cefr_level
        if data.duration_minutes: exam.duration_minutes = data.duration_minutes
        if data.language: exam.language = data.language
        if data.total_questions: exam.total_questions = data.total_questions

        # Qismlarni yangilash (eskisini o'chirib yangisini yozadi)
        if data.parts is not None:
            exam.parts.clear() 
            for p_data in data.parts:
                part = ReadingPart(title=p_data.title, description=p_data.description, passage=p_data.passage)
                for q_idx, q_data in enumerate(p_data.questions):
                    question = Question(
                        question_number=q_data.question_number or (q_idx + 1),
                        type=q_data.type, text=q_data.text, correct_answer=q_data.correct_answer,
                        word_limit=q_data.word_limit
                    )
                    for opt in (q_data.options or []):
                        question.options.append(QuestionOption(label=opt.label, value=opt.value))
                    part.questions.append(question)
                exam.parts.append(part)

        await self.db.commit()
        return await self.get_exam(exam.id)

    # ----------------------------------------------------------------
    # 4. SUBMIT: Javoblarni tekshirish va natijani hisoblash
    # ----------------------------------------------------------------
    async def submit_exam_and_get_result(self, user_id: int, data: ResultSubmission):
        exam = await self.get_exam(data.exam_id)
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        correct_count = 0
        total_q = 0
        review_items = []

        for part in exam.parts:
            for q in part.questions:
                total_q += 1
                q_id_str = str(q.id)
                user_ans = data.user_answers.get(q_id_str, "").strip().lower()
                correct_ans = q.correct_answer.strip().lower()
                
                # Ko'p variantli javoblar (apple/an apple)
                valid_options = [a.strip() for a in correct_ans.split("/")]
                is_correct = user_ans in valid_options
                
                if is_correct:
                    correct_count += 1
                
                review_items.append({
                    "question_number": q.question_number,
                    "user_answer": user_ans,
                    "correct_answer": q.correct_answer,
                    "is_correct": is_correct,
                    "type": q.type
                })

        std_score, level = self._calculate_metrics(correct_count, total_q)
        
        new_result = ExamResult(
            user_id=user_id,
            exam_id=exam.id,
            raw_score=correct_count,
            standard_score=float(std_score),
            cefr_level=level,
            percentage=(correct_count / total_q) * 100 if total_q > 0 else 0,
            user_answers=data.user_answers
        )
        
        self.db.add(new_result)
        await self.db.commit()
        await self.db.refresh(new_result)
        
        return {
            "summary": new_result,
            "review": review_items
        }

    # ----------------------------------------------------------------
    # 5. REVIEW & LIST & METRICS
    # ----------------------------------------------------------------
    async def get_result_with_review(self, result_id: int, user_id: int):
        stmt = select(ExamResult).where(ExamResult.id == result_id, ExamResult.user_id == user_id)
        res = await self.db.execute(stmt)
        result_obj = res.scalar_one_or_none()
        
        if not result_obj:
            return None

        exam = await self.get_exam(result_obj.exam_id)
        review_data = []
        
        for part in exam.parts:
            for q in part.questions:
                u_ans = result_obj.user_answers.get(str(q.id), "")
                review_data.append({
                    "question_number": q.question_number,
                    "user_answer": u_ans,
                    "correct_answer": q.correct_answer,
                    "is_correct": u_ans.strip().lower() == q.correct_answer.strip().lower(),
                    "type": q.type
                })
        
        return {"summary": result_obj, "review": review_data}

    async def get_all_exams(self):
        stmt = select(Exam).options(selectinload(Exam.parts))
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()

    async def get_user_results(self, user_id: int):
        stmt = select(ExamResult).where(ExamResult.user_id == user_id).order_by(ExamResult.created_at.desc())
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def delete_exam(self, exam_id: str) -> bool:
        exam = await self.get_exam(exam_id)
        if not exam: return False
        await self.db.delete(exam)
        await self.db.commit()
        return True

    def _calculate_metrics(self, correct: int, total: int):
        if correct >= 28:
            return 65 + (correct - 28) * 1.4, "C1"
        if correct >= 18:
            return 51 + (correct - 18) * 1.4, "B2"
        if correct >= 10:
            return 38 + (correct - 10) * 1.4, "B1"
        return correct * 2, "B1 dan past"