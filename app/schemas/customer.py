from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr


class CustomerRead(ORMModel):
    id: int
    name: str
    email: str
    created_at: datetime


class CurrencyBalance(BaseModel):
    currency: str
    total_invoiced: Decimal
    total_paid: Decimal
    outstanding: Decimal


class CustomerBalance(BaseModel):
    customer_id: int
    balances: list[CurrencyBalance]
