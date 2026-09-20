from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Customer(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    name: str = Field(
        index=True,
    )

    email: Optional[str] = Field(
        default=None,
        index=True,
    )

    phone: Optional[str] = Field(
        default=None,
        index=True,
    )

    company: Optional[str] = None

    status: str = Field(
        default="lead",
        index=True,
    )

    notes: Optional[str] = None

    created_at: datetime = Field(
        default_factory=utc_now,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
    )


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    action: str = Field(
        index=True,
    )

    description: str

    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

    created_at: datetime = Field(
        default_factory=utc_now,
    )


class Currency(SQLModel, table=True):
    code: str = Field(
        primary_key=True,
        max_length=3,
    )

    symbol: str
    name: str
    active: bool = True


class PricingRule(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    service_code: str = Field(
        index=True,
    )

    currency_code: str = Field(
        index=True,
    )

    unit_name: str

    unit_price: Decimal

    minimum_units: int = 1

    maximum_units: Optional[int] = None

    active: bool = True

    created_at: datetime = Field(
        default_factory=utc_now,
    )