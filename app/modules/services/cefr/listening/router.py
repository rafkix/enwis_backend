from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from .services import ListeningService
from .schemas import (
    ListeningExamResponse, 
    ListeningExamCreate, 
    ListeningExamUpdate,
    ListeningResultCreate,
    ListeningResultResponse,
    ListeningSubmission
)

router = APIRouter(prefix="/services/cefr/listening", tags=["Listening CEFR"])

@router.post("/create", response_model=ListeningExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(data: ListeningExamCreate, db: AsyncSession = Depends(get_db)):
    service = ListeningService(db)
    return await service.create_exam(data)

@router.post("/submit", status_code=status.HTTP_200_OK)
async def submit_exam(
    submission: ListeningSubmission, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = ListeningService(db)
    return await service.submit_exam_and_get_result(
        user_id=current_user.id, 
        exam_id=submission.exam_id, 
        user_answers=submission.user_answers
    )
    
@router.get("/my-results", response_model=List[ListeningResultResponse])
async def get_my_results(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = ListeningService(db)
    return await service.get_user_results(current_user.id)

@router.get("/result/{result_id}")
async def get_result_detail(
    result_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = ListeningService(db)
    return await service.get_result_details(result_id, current_user.id)

@router.get("/list", response_model=List[ListeningExamResponse])
async def get_all_exams(db: AsyncSession = Depends(get_db)):
    service = ListeningService(db)
    return await service.get_all_exams()

@router.get("/{exam_id}", response_model=ListeningExamResponse)
async def get_exam_by_id(exam_id: str, db: AsyncSession = Depends(get_db)):
    service = ListeningService(db)
    return await service.get_exam_by_id(exam_id)

@router.put("/{exam_id}", response_model=ListeningExamResponse)
async def update_exam(
    exam_id: str, 
    data: ListeningExamCreate, # To'liq yangilash uchun Create sxemasini ishlatamiz
    db: AsyncSession = Depends(get_db)
):
    service = ListeningService(db)
    return await service.update_exam(exam_id, data)

@router.delete("/{exam_id}", status_code=status.HTTP_200_OK)
async def delete_exam(exam_id: str, db: AsyncSession = Depends(get_db)):
    service = ListeningService(db)
    return await service.delete_exam(exam_id)