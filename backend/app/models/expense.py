import uuid
from datetime import date

from sqlalchemy import BigInteger, Date, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    amount_paisa: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, server_default="")
    date: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        Index("idx_expenses_category", "category"),
        Index("idx_expenses_date", "date"),
    )
