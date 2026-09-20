from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.main import app
from app.database.database import create_db_and_tables
from app.models.shared import Customer
from app.models.payflow import Invoice, InvoiceItem, Payment, PaymentReminder
from app.services.payflow import (
    calculate_invoice_totals,
    create_invoice,
    create_reminder,
    record_payment,
)


client = TestClient(app)

create_db_and_tables()


def create_test_customer():
    with Session(
        __import__("app.database.database", fromlist=["engine"]).engine
    ) as session:
        customer = Customer(
            name="PayFlow Test Customer",
            email="payflow@example.com",
            phone="08000000000",
        )

        session.add(customer)
        session.commit()
        session.refresh(customer)

        return customer.id


def test_payflow_dashboard():
    response = client.get("/payflow")

    assert response.status_code == 200
    assert "PayFlow" in response.text


def test_invoice_creation_and_totals():
    customer_id = create_test_customer()

    from app.database.database import engine

    with Session(engine) as session:
        invoice = create_invoice(
            session=session,
            customer_id=customer_id,
            currency="NGN",
            due_date=None,
            notes="Test invoice",
            items=[
                {
                    "description": "Consulting",
                    "quantity": Decimal("2"),
                    "unit_price": Decimal("5000"),
                },
                {
                    "description": "Setup",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("2500"),
                },
            ],
        )

        assert invoice.invoice_number.startswith("INV-")
        assert invoice.currency == "NGN"
        assert invoice.subtotal == Decimal("12500.00")
        assert invoice.total == Decimal("12500.00")
        assert invoice.amount_paid == Decimal("0.00")
        assert invoice.balance_due == Decimal("12500.00")
        assert invoice.status == "unpaid"


def test_invoice_number_is_unique():
    customer_id = create_test_customer()

    from app.database.database import engine

    with Session(engine) as session:
        invoice_one = create_invoice(
            session=session,
            customer_id=customer_id,
            currency="NGN",
            due_date=None,
            notes=None,
            items=[
                {
                    "description": "Service A",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("1000"),
                }
            ],
        )

        invoice_two = create_invoice(
            session=session,
            customer_id=customer_id,
            currency="NGN",
            due_date=None,
            notes=None,
            items=[
                {
                    "description": "Service B",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("2000"),
                }
            ],
        )

        assert invoice_one.invoice_number != invoice_two.invoice_number


def test_partial_payment_updates_balance():
    customer_id = create_test_customer()

    from app.database.database import engine

    with Session(engine) as session:
        invoice = create_invoice(
            session=session,
            customer_id=customer_id,
            currency="NGN",
            due_date=None,
            notes=None,
            items=[
                {
                    "description": "Service",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("10000"),
                }
            ],
        )

        payment = record_payment(
            session=session,
            invoice=invoice,
            amount=Decimal("4000"),
            method="bank_transfer",
            reference="TEST-001",
        )

        session.refresh(invoice)

        assert payment.amount == Decimal("4000.00")
        assert invoice.amount_paid == Decimal("4000.00")
        assert invoice.balance_due == Decimal("6000.00")
        assert invoice.status == "partially_paid"


def test_full_payment_marks_invoice_paid():
    customer_id = create_test_customer()

    from app.database.database import engine

    with Session(engine) as session:
        invoice = create_invoice(
            session=session,
            customer_id=customer_id,
            currency="NGN",
            due_date=None,
            notes=None,
            items=[
                {
                    "description": "Service",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("7500"),
                }
            ],
        )

        record_payment(
            session=session,
            invoice=invoice,
            amount=Decimal("7500"),
            method="manual",
        )

        session.refresh(invoice)

        assert invoice.amount_paid == Decimal("7500.00")
        assert invoice.balance_due == Decimal("0.00")
        assert invoice.status == "paid"


def test_overpayment_is_rejected():
    customer_id = create_test_customer()

    from app.database.database import engine

    with Session(engine) as session:
        invoice = create_invoice(
            session=session,
            customer_id=customer_id,
            currency="NGN",
            due_date=None,
            notes=None,
            items=[
                {
                    "description": "Service",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("5000"),
                }
            ],
        )

        with pytest.raises(ValueError, match="exceed"):
            record_payment(
                session=session,
                invoice=invoice,
                amount=Decimal("5001"),
            )


def test_zero_payment_is_rejected():
    customer_id = create_test_customer()

    from app.database.database import engine

    with Session(engine) as session:
        invoice = create_invoice(
            session=session,
            customer_id=customer_id,
            currency="NGN",
            due_date=None,
            notes=None,
            items=[
                {
                    "description": "Service",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("5000"),
                }
            ],
        )

        with pytest.raises(ValueError, match="greater than zero"):
            record_payment(
                session=session,
                invoice=invoice,
                amount=Decimal("0"),
            )


def test_payment_reminder_creation():
    customer_id = create_test_customer()

    from app.database.database import engine

    with Session(engine) as session:
        invoice = create_invoice(
            session=session,
            customer_id=customer_id,
            currency="NGN",
            due_date=None,
            notes=None,
            items=[
                {
                    "description": "Service",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("3000"),
                }
            ],
        )

        reminder = create_reminder(
            session=session,
            invoice=invoice,
            message="Payment is due.",
        )

        assert reminder.id is not None
        assert reminder.invoice_id == invoice.id
        assert reminder.message == "Payment is due."
        assert reminder.sent is False


def test_invoice_detail_page():
    customer_id = create_test_customer()

    from app.database.database import engine

    with Session(engine) as session:
        invoice = create_invoice(
            session=session,
            customer_id=customer_id,
            currency="NGN",
            due_date=None,
            notes="Invoice page test",
            items=[
                {
                    "description": "Service",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("2000"),
                }
            ],
        )

        invoice_id = invoice.id

    response = client.get(f"/payflow/invoices/{invoice_id}")

    assert response.status_code == 200
    assert invoice.invoice_number in response.text
    assert "Invoice page test" in response.text
    assert "2000.00" in response.text