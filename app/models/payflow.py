from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_number: str = Field(index=True, unique=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)

    currency: str = Field(default="NGN", max_length=10)
    issue_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None

    notes: Optional[str] = None
    status: str = Field(default="unpaid", index=True)

    subtotal: Decimal = Field(default=Decimal("0.00"))
    amount_paid: Decimal = Field(default=Decimal("0.00"))
    total: Decimal = Field(default=Decimal("0.00"))
    balance_due: Decimal = Field(default=Decimal("0.00"))


class InvoiceItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id", index=True)

    description: str
    quantity: Decimal = Field(default=Decimal("1.00"))
    unit_price: Decimal = Field(default=Decimal("0.00"))
    line_total: Decimal = Field(default=Decimal("0.00"))


class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id", index=True)

    amount: Decimal = Field(default=Decimal("0.00"))
    currency: str = Field(default="NGN", max_length=10)
    payment_date: datetime = Field(default_factory=datetime.utcnow)

    method: str = Field(default="manual")
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentReminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id", index=True)

    reminder_date: datetime = Field(default_factory=datetime.utcnow)
    message: str
    sent: bool = Field(default=False)
