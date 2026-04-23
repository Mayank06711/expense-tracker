from datetime import date
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.repositories.expense_repo import ExpenseRepository
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseListResponse
from app.utils.money import rupees_to_paisa, paisa_to_rupees


class ExpenseService:
    def __init__(self, repo: ExpenseRepository):
        self.repo = repo

    async def create_expense(self, session: AsyncSession, data: ExpenseCreate) -> tuple[ExpenseResponse, bool]:
        """Returns (expense, was_replay). was_replay=True if this was a duplicate UUID."""
        amount_paisa = rupees_to_paisa(data.amount)

        expense = Expense(
            id=data.id,
            amount_paisa=amount_paisa,
            category=data.category,
            description=data.description,
            date=data.date,
        )

        try:
            async with session.begin():
                created = await self.repo.create(session, expense)
                return self._to_response(created), False
        except IntegrityError:
            await session.rollback()
            existing = await self.repo.get_by_id(session, data.id)
            if existing is None:
                raise RuntimeError("Integrity error but record not found - unexpected state")
            return self._to_response(existing), True

    async def list_expenses(
        self,
        session: AsyncSession,
        category: Optional[str] = None,
        sort: str = "date_desc",
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> ExpenseListResponse:
        expenses = await self.repo.list_all(session, category=category, sort=sort, from_date=from_date, to_date=to_date)
        total_paisa = await self.repo.get_total_paisa(session, category=category, from_date=from_date, to_date=to_date)

        return ExpenseListResponse(
            expenses=[self._to_response(e) for e in expenses],
            total_amount=paisa_to_rupees(total_paisa),
            count=len(expenses),
        )

    async def delete_expense(self, session: AsyncSession, expense_id) -> bool:
        async with session.begin():
            return await self.repo.delete(session, expense_id)

    async def get_summary(self, session: AsyncSession) -> dict:
        rows = await self.repo.get_category_summary(session)
        total_paisa = sum(r["total_paisa"] for r in rows)

        return {
            "total": paisa_to_rupees(total_paisa),
            "by_category": [
                {
                    "category": r["category"],
                    "total": paisa_to_rupees(r["total_paisa"]),
                    "count": r["count"],
                }
                for r in rows
            ],
        }

    def _to_response(self, expense: Expense) -> ExpenseResponse:
        return ExpenseResponse(
            id=expense.id,
            amount=paisa_to_rupees(expense.amount_paisa),
            category=expense.category,
            description=expense.description,
            date=expense.date,
            created_at=expense.created_at,
        )
