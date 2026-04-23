import uuid
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from pydantic import BaseModel, field_validator, Field


class ExpenseCreate(BaseModel):
    id: uuid.UUID
    amount: str = Field(..., description="Amount in rupees as string, e.g. '150.50'")
    category: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=500)
    date: date

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: str) -> str:
        try:
            val = Decimal(v)
        except InvalidOperation:
            raise ValueError("Amount must be a valid number")
        if val <= 0:
            raise ValueError("Amount must be greater than zero")
        if val > Decimal("9999999.99"):
            raise ValueError("Amount exceeds maximum (₹99,99,999.99)")
        if val != val.quantize(Decimal("0.01")):
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("Category cannot be empty")
        return v

    @field_validator("description")
    @classmethod
    def normalize_description(cls, v: str) -> str:
        return v.strip()

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date) -> date:
        # Expense can never be in the future — you can't spend money tomorrow
        # Use +1 day buffer only for timezone edge cases (user's "today" may be server's "tomorrow")
        today_utc = datetime.now(timezone.utc).date()
        max_date = today_utc + timedelta(days=1)  # timezone buffer only, not "future allowed"
        if v > max_date:
            raise ValueError("Expense date cannot be in the future")
        return v


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    amount: str
    category: str
    description: str
    date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    expenses: list[ExpenseResponse]
    total_amount: str
    count: int


class ExpenseFilter(BaseModel):
    category: Optional[str] = None
    sort: Optional[str] = "date_desc"
    from_date: Optional[date] = None
    to_date: Optional[date] = None

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v: str) -> str:
        allowed = {"date_desc", "date_asc"}
        if v not in allowed:
            raise ValueError(f"Sort must be one of: {', '.join(allowed)}")
        return v
