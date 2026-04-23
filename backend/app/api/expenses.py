from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_expense_service
from app.schemas.expense import ExpenseCreate, ExpenseFilter
from app.schemas.response import SuccessResponse
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _meta(request: Request, extra: dict = None) -> dict:
    meta = {
        "request_id": getattr(request.state, "request_id", None),
        "timestamp": getattr(request.state, "timestamp", None),
    }
    if extra:
        meta.update(extra)
    return meta


@router.post("", status_code=201)
async def create_expense(
    request: Request,
    body: ExpenseCreate,
    session: AsyncSession = Depends(get_session),
    service: ExpenseService = Depends(get_expense_service),
):
    expense, was_replay = await service.create_expense(session, body)
    resp = SuccessResponse(
        status=201,
        message="Expense created successfully",
        data=expense.model_dump(mode="json"),
        metadata=_meta(request),
    )
    response = JSONResponse(content=resp.model_dump(mode="json"), status_code=201)
    if was_replay:
        response.headers["X-Idempotent-Replayed"] = "true"
    return response


@router.get("")
async def list_expenses(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    sort: str = Query("date_desc", description="Sort order: date_desc or date_asc"),
    from_date: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_session),
    service: ExpenseService = Depends(get_expense_service),
):
    try:
        filters = ExpenseFilter(category=category, sort=sort, from_date=from_date, to_date=to_date)
    except ValidationError as e:
        errors = e.errors()
        field_errors = {str(err["loc"][-1]): err["msg"] for err in errors}
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "Invalid query parameters",
                "error_code": "VALIDATION_ERROR",
                "metadata": {"fields": field_errors, **_meta(request)},
            },
        )

    result = await service.list_expenses(
        session,
        category=filters.category,
        sort=filters.sort,
        from_date=filters.from_date,
        to_date=filters.to_date,
    )
    return SuccessResponse(
        status=200,
        message="Expenses retrieved",
        data=result.model_dump(mode="json"),
        metadata=_meta(request, {
            "filters": {
                "category": filters.category,
                "from_date": str(filters.from_date) if filters.from_date else None,
                "to_date": str(filters.to_date) if filters.to_date else None,
            },
            "sort": filters.sort,
        }),
    )


@router.delete("/{expense_id}")
async def delete_expense(
    request: Request,
    expense_id: UUID,
    session: AsyncSession = Depends(get_session),
    service: ExpenseService = Depends(get_expense_service),
):
    deleted = await service.delete_expense(session, expense_id)
    if not deleted:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "Expense not found",
                "error_code": "NOT_FOUND",
                "metadata": _meta(request),
            },
        )
    return SuccessResponse(
        status=200,
        message="Expense deleted",
        data={"id": str(expense_id)},
        metadata=_meta(request),
    )


@router.get("/summary")
async def expense_summary(
    request: Request,
    session: AsyncSession = Depends(get_session),
    service: ExpenseService = Depends(get_expense_service),
):
    summary = await service.get_summary(session)
    return SuccessResponse(
        status=200,
        message="Expense summary",
        data=summary,
        metadata=_meta(request),
    )
