from fastapi import APIRouter

from src.api.v1.documents import router as documents_router

router = APIRouter(prefix="/api/v1")
router.include_router(documents_router)
