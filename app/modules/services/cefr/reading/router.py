from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
# Modellaringiz joylashuviga qarab import yo'llarini tekshiring
from .schemas import (
    ExamCreate, 
    ExamUpdate, 
    ExamResponse, 
    ResultSubmission, 
    ResultResponse,
    ReadingResultDetailResponse # Review sahifasi uchun schema
)
from .services import ReadingExamService

router = APIRouter(
    prefix="/services/cefr/reading",
    tags=["CEFR Reading"]
)

# --- IMTIHON BOSHQARUVI (ADMIN/MODERATOR) ---

@router.post("/create", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    payload: ExamCreate,
    db: AsyncSession = Depends(get_db)
):
    """Yangi Reading imtihoni yaratish."""
    service = ReadingExamService(db)
    # ID unikal ekanligini tekshirish
    if await service.get_exam(payload.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Bu ID bilan imtihon allaqachon mavjud"
        )
    return await service.create_exam(payload)

@router.get("/list", response_model=List[ExamResponse])
async def list_exams(db: AsyncSession = Depends(get_db)):
    """Barcha mavjud imtihonlar ro'yxatini olish."""
    return await ReadingExamService(db).get_all_exams()

@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(exam_id: str, db: AsyncSession = Depends(get_db)):
    """Muayyan imtihonni barcha qismlari va savollari bilan olish."""
    exam = await ReadingExamService(db).get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Imtihon topilmadi")
    return exam

@router.put("/update/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: str,
    data: ExamUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Imtihon ma'lumotlarini yangilash."""
    service = ReadingExamService(db)
    updated_exam = await service.update_exam(exam_id, data)
    if not updated_exam:
        raise HTTPException(status_code=404, detail="Imtihon topilmadi")
    return updated_exam

@router.delete("/delete/{exam_id}")
async def delete_exam(exam_id: str, db: AsyncSession = Depends(get_db)):
    """Imtihonni o'chirish."""
    service = ReadingExamService(db)
    if not await service.delete_exam(exam_id):
        raise HTTPException(status_code=404, detail="Imtihon topilmadi")
    return {"success": True, "message": "Imtihon muvaffaqiyatli o'chirildi"}

# --- NATIJALAR VA TOPSHIRISH (USER) ---

@router.post("/submit", response_model=ReadingResultDetailResponse)
async def submit_exam(
    payload: ResultSubmission,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Imtihon javoblarini topshirish va natijani hisoblash."""
    service = ReadingExamService(db)
    return await service.submit_exam_and_get_result(user.id, payload)

@router.get("/results/my", response_model=List[ResultResponse])
async def get_my_results(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Foydalanuvchining barcha topshirgan imtihonlari natijalari."""
    service = ReadingExamService(db)
    return await service.get_user_results(user.id)

@router.get("/results/{result_id}", response_model=ReadingResultDetailResponse)
async def get_result_detail(
    result_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Muayyan natijani tahlili (review) bilan birga ko'rish."""
    # Eslatma: get_result_with_review funksiyasini servisga qo'shishingiz kerak bo'ladi
    # yoki submit funksiyasi kabi barcha detallarni qaytaradigan mantiq yoziladi
    service = ReadingExamService(db)
    # Agar servisda bu funksiya hali yo'q bo'lsa, uni qo'shish tavsiya etiladi
    result = await service.get_result_with_review(result_id, user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Natija topilmadi")
    return result