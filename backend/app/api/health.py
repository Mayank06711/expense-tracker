from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.response import SuccessResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(request: Request, session: AsyncSession = Depends(get_session)):
    await session.execute(text("SELECT 1"))
    return SuccessResponse(
        status=200,
        message="Healthy",
        data={"db": "connected"},
        metadata={
            "request_id": getattr(request.state, "request_id", None),
            "timestamp": getattr(request.state, "timestamp", None),
        },
    )
