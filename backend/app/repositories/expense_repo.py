from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository):

    async def create(self, session: AsyncSession, expense: Expense) -> Expense:
        session.add(expense)
        await session.flush()
        return expense

    async def get_by_id(self, session: AsyncSession, expense_id: UUID) -> Optional[Expense]:
        result = await session.execute(
            select(Expense).where(Expense.id == expense_id)
        )
        return result.scalar_one_or_none()

    def _apply_filters(self, query, category=None, from_date=None, to_date=None):
        if category:
            query = query.where(Expense.category == category.strip().lower())
        if from_date:
            query = query.where(Expense.date >= from_date)
        if to_date:
            query = query.where(Expense.date <= to_date)
        return query

    async def list_all(
        self,
        session: AsyncSession,
        category: Optional[str] = None,
        sort: str = "date_desc",
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[Expense]:
        query = select(Expense)
        query = self._apply_filters(query, category, from_date, to_date)

        if sort == "date_asc":
            query = query.order_by(Expense.date.asc(), Expense.created_at.asc())
        else:
            query = query.order_by(Expense.date.desc(), Expense.created_at.desc())

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_total_paisa(
        self,
        session: AsyncSession,
        category: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> int:
        query = select(func.coalesce(func.sum(Expense.amount_paisa), 0))
        query = self._apply_filters(query, category, from_date, to_date)

        result = await session.execute(query)
        return result.scalar_one()

    async def delete(self, session: AsyncSession, expense_id: UUID) -> bool:
        expense = await self.get_by_id(session, expense_id)
        if not expense:
            return False
        await session.delete(expense)
        await session.flush()
        return True

    async def get_category_summary(
        self,
        session: AsyncSession,
    ) -> list[dict]:
        query = (
            select(
                Expense.category,
                func.sum(Expense.amount_paisa).label("total_paisa"),
                func.count(Expense.id).label("count"),
            )
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount_paisa).desc())
        )
        result = await session.execute(query)
        return [
            {"category": row.category, "total_paisa": row.total_paisa, "count": row.count}
            for row in result.all()
        ]
