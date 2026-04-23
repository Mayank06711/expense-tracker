from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.expense_repo import ExpenseRepository
from app.services.expense_service import ExpenseService


def get_expense_repo() -> ExpenseRepository:
    return ExpenseRepository()


def get_expense_service(
    repo: ExpenseRepository = Depends(get_expense_repo),
) -> ExpenseService:
    return ExpenseService(repo=repo)
