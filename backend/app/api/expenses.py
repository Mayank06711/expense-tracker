from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_expense_service
from app.schemas.expense import ExpenseCreate, ExpenseFilter
from app.schemas.response import SuccessResponse
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", status_code=201)
async def create_expense(
    body: ExpenseCreate,
    session: AsyncSession = Depends(get_session),
    service: ExpenseService = Depends(get_expense_service),
):
    expense = await service.create_expense(session, body)
    return SuccessResponse(
        status=201,
        message="Expense created successfully",
        data=expense.model_dump(mode="json"),
        metadata={},
    )


@router.get("")
async def list_expenses(
    category: Optional[str] = Query(None, description="Filter by category"),
    sort: str = Query("date_desc", description="Sort order: date_desc or date_asc"),
    session: AsyncSession = Depends(get_session),
    service: ExpenseService = Depends(get_expense_service),
):
    try:
        filters = ExpenseFilter(category=category, sort=sort)
    except ValidationError as e:
        errors = e.errors()
        field_errors = {str(err["loc"][-1]): err["msg"] for err in errors}
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "Invalid query parameters",
                "error_code": "VALIDATION_ERROR",
                "metadata": {"fields": field_errors},
            },
        )

    result = await service.list_expenses(
        session,
        category=filters.category,
        sort=filters.sort,
    )
    return SuccessResponse(
        status=200,
        message="Expenses retrieved",
        data=result.model_dump(mode="json"),
        metadata={
            "filters": {"category": filters.category},
            "sort": filters.sort,
        },
    )


@router.get("/summary")
async def expense_summary(
    session: AsyncSession = Depends(get_session),
    service: ExpenseService = Depends(get_expense_service),
):
    summary = await service.get_summary(session)
    return SuccessResponse(
        status=200,
        message="Expense summary",
        data=summary,
        metadata={},
    )
