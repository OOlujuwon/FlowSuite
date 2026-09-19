from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Customer(SQLModel, table=True):
    """
    Shared customer record.

    ClientFlow will eventually provide the main interface for managing
    these records. PayFlow will reference customers when creating invoices.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(index=True)
    email: Optional[str] = Field(default=None, index=True)
    phone: Optional[str] = Field(default=None, index=True)

    company: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Activity(SQLModel, table=True):
    """
    Shared activity log.

    This gives the system a common history trail for future CRM,
    payment, cleanup and automation actions.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    action: str = Field(index=True)
    description: str

    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

    created_at: datetime = Field(default_factory=utc_now)


class Currency(SQLModel, table=True):
    """
    Currency configuration.

    Prices are stored as decimal values rather than floating-point numbers.
    """

    code: str = Field(primary_key=True, max_length=3)
    symbol: str
    name: str

    active: bool = True


class PricingRule(SQLModel, table=True):
    """
    Generic pricing configuration.

    This deliberately does not lock FlowSuite into subscriptions,
    wallets or customer accounts.

    Each service can later calculate a one-time purchase from these rules.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    service_code: str = Field(index=True)
    currency_code: str = Field(index=True)

    unit_name: str
    unit_price: Decimal

    minimum_units: int = 1
    maximum_units: Optional[int] = None

    active: bool = True

    created_at: datetime = Field(default_factory=utc_now)