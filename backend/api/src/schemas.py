from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import AnyUrl, BaseModel, Field, condecimal


Currency = Literal["RUB", "USD", "EUR"]
PaymentStatus = Literal["pending", "succeeded", "failed"]

Amount = condecimal(gt=0, max_digits=18, decimal_places=2)


class PaymentCreate(BaseModel):
    amount: Amount = Field(..., examples=["100.00"])
    currency: Currency
    description: str = Field(..., min_length=1, max_length=10_000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: AnyUrl


class PaymentAccepted(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class PaymentDetail(BaseModel):
    payment_id: UUID
    amount: Amount = Field(..., examples=["100.00"])
    currency: Currency
    description: str
    metadata: dict[str, Any]
    webhook_url: AnyUrl | None
    status: PaymentStatus
    created_at: datetime
    processed_at: datetime | None

