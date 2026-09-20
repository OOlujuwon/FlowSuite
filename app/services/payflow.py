from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlmodel import Session, select

from app.models.payflow import (
    Invoice,
    InvoiceItem,
    Payment,
    PaymentReminder,
)

TWOPLACES = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_invoice_number(session: Session) -> str:
    year = datetime.utcnow().year
    prefix = f"INV-{year}-"

    invoices = session.exec(
        select(Invoice).where(Invoice.invoice_number.startswith(prefix))
    ).all()

    highest = 0

    for invoice in invoices:
        try:
            number = int(invoice.invoice_number.split("-")[-1])
            highest = max(highest, number)
        except (ValueError, IndexError):
            continue

    return f"{prefix}{highest + 1:05d}"


def calculate_invoice_totals(session: Session, invoice: Invoice) -> Invoice:
    items = session.exec(
        select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)
    ).all()

    subtotal = sum(
        (money(item.line_total) for item in items),
        Decimal("0.00"),
    )

    paid = sum(
        (
            money(payment.amount)
            for payment in session.exec(
                select(Payment).where(Payment.invoice_id == invoice.id)
            ).all()
        ),
        Decimal("0.00"),
    )

    total = money(subtotal)
    balance = max(money(total - paid), Decimal("0.00"))

    invoice.subtotal = subtotal
    invoice.total = total
    invoice.amount_paid = paid
    invoice.balance_due = balance

    if balance <= Decimal("0.00"):
        invoice.status = "paid"
    elif paid > Decimal("0.00"):
        invoice.status = "partially_paid"
    elif invoice.due_date and invoice.due_date < datetime.utcnow():
        invoice.status = "overdue"
    else:
        invoice.status = "unpaid"

    session.add(invoice)
    session.commit()
    session.refresh(invoice)

    return invoice


def create_invoice(
    session: Session,
    customer_id: int,
    currency: str,
    due_date: Optional[datetime],
    notes: Optional[str],
    items: list[dict],
) -> Invoice:
    invoice = Invoice(
        invoice_number=generate_invoice_number(session),
        customer_id=customer_id,
        currency=currency,
        due_date=due_date,
        notes=notes,
    )

    session.add(invoice)
    session.commit()
    session.refresh(invoice)

    for item_data in items:
        quantity = money(item_data["quantity"])
        unit_price = money(item_data["unit_price"])
        line_total = money(quantity * unit_price)

        item = InvoiceItem(
            invoice_id=invoice.id,
            description=item_data["description"],
            quantity=quantity,
            unit_price=unit_price,
            line_total=line_total,
        )

        session.add(item)

    session.commit()

    return calculate_invoice_totals(session, invoice)


def record_payment(
    session: Session,
    invoice: Invoice,
    amount,
    method: str = "manual",
    reference: Optional[str] = None,
    notes: Optional[str] = None,
) -> Payment:
    amount = money(amount)

    if amount <= Decimal("0.00"):
        raise ValueError("Payment amount must be greater than zero.")

    if amount > money(invoice.balance_due):
        raise ValueError("Payment cannot exceed the outstanding balance.")

    payment = Payment(
        invoice_id=invoice.id,
        amount=amount,
        currency=invoice.currency,
        method=method,
        reference=reference,
        notes=notes,
    )

    session.add(payment)
    session.commit()
    session.refresh(payment)

    calculate_invoice_totals(session, invoice)

    return payment


def create_reminder(
    session: Session,
    invoice: Invoice,
    message: str,
) -> PaymentReminder:
    reminder = PaymentReminder(
        invoice_id=invoice.id,
        message=message,
    )

    session.add(reminder)
    session.commit()
    session.refresh(reminder)

    return reminder
