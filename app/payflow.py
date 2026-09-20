from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database.database import engine
from app.models.shared import Customer
from app.models.payflow import Invoice, InvoiceItem, Payment, PaymentReminder
from app.services.payflow import (
    calculate_invoice_totals,
    create_invoice,
    create_reminder,
    record_payment,
)

router = APIRouter(prefix="/payflow", tags=["PayFlow"])
templates = Jinja2Templates(directory="templates")


def get_customer(session: Session, customer_id: int) -> Customer:
    customer = session.get(Customer, customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    return customer


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    with Session(engine) as session:
        invoices = session.exec(
            select(Invoice).order_by(Invoice.id.desc())
        ).all()

        total_invoiced = sum(
            (invoice.total for invoice in invoices),
            Decimal("0.00"),
        )

        total_paid = sum(
            (invoice.amount_paid for invoice in invoices),
            Decimal("0.00"),
        )

        total_outstanding = sum(
            (invoice.balance_due for invoice in invoices),
            Decimal("0.00"),
        )

        return templates.TemplateResponse(
            request=request,
            name="payflow/dashboard.html",
            context={
                "invoices": invoices,
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "total_outstanding": total_outstanding,
            },
        )


@router.get("/invoices/new", response_class=HTMLResponse)
def new_invoice(request: Request):
    with Session(engine) as session:
        customers = session.exec(
            select(Customer).order_by(Customer.name)
        ).all()

        return templates.TemplateResponse(
            request=request,
            name="payflow/invoice_form.html",
            context={"customers": customers},
        )


@router.post("/invoices/new")
def create_new_invoice(
    customer_id: int = Form(...),
    currency: str = Form("NGN"),
    due_date: str = Form(""),
    notes: str = Form(""),
    description: str = Form(...),
    quantity: Decimal = Form(...),
    unit_price: Decimal = Form(...),
):
    with Session(engine) as session:
        get_customer(session, customer_id)

        parsed_due_date: Optional[datetime] = None

        if due_date:
            try:
                parsed_due_date = datetime.fromisoformat(due_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid due date.",
                )

        try:
            invoice = create_invoice(
                session=session,
                customer_id=customer_id,
                currency=currency.upper(),
                due_date=parsed_due_date,
                notes=notes.strip() or None,
                items=[
                    {
                        "description": description.strip(),
                        "quantity": quantity,
                        "unit_price": unit_price,
                    }
                ],
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return RedirectResponse(
            url=f"/payflow/invoices/{invoice.id}",
            status_code=303,
        )


@router.get("/invoices/{invoice_id}", response_class=HTMLResponse)
def invoice_detail(request: Request, invoice_id: int):
    with Session(engine) as session:
        invoice = session.get(Invoice, invoice_id)

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        customer = get_customer(session, invoice.customer_id)

        items = session.exec(
            select(InvoiceItem).where(
                InvoiceItem.invoice_id == invoice.id
            )
        ).all()

        payments = session.exec(
            select(Payment)
            .where(Payment.invoice_id == invoice.id)
            .order_by(Payment.payment_date.desc())
        ).all()

        reminders = session.exec(
            select(PaymentReminder)
            .where(PaymentReminder.invoice_id == invoice.id)
            .order_by(PaymentReminder.reminder_date.desc())
        ).all()

        return templates.TemplateResponse(
            request=request,
            name="payflow/invoice_detail.html",
            context={
                "invoice": invoice,
                "customer": customer,
                "items": items,
                "payments": payments,
                "reminders": reminders,
            },
        )


@router.post("/invoices/{invoice_id}/payments")
def add_payment(
    invoice_id: int,
    amount: Decimal = Form(...),
    method: str = Form("manual"),
    reference: str = Form(""),
    notes: str = Form(""),
):
    with Session(engine) as session:
        invoice = session.get(Invoice, invoice_id)

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        try:
            record_payment(
                session=session,
                invoice=invoice,
                amount=amount,
                method=method.strip() or "manual",
                reference=reference.strip() or None,
                notes=notes.strip() or None,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return RedirectResponse(
            url=f"/payflow/invoices/{invoice_id}",
            status_code=303,
        )


@router.post("/invoices/{invoice_id}/reminders")
def add_reminder(
    invoice_id: int,
    message: str = Form(...),
):
    with Session(engine) as session:
        invoice = session.get(Invoice, invoice_id)

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        create_reminder(
            session=session,
            invoice=invoice,
            message=message.strip(),
        )

        return RedirectResponse(
            url=f"/payflow/invoices/{invoice_id}",
            status_code=303,
        )


@router.get("/invoices/{invoice_id}/print", response_class=HTMLResponse)
def print_invoice(request: Request, invoice_id: int):
    with Session(engine) as session:
        invoice = session.get(Invoice, invoice_id)

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        customer = get_customer(session, invoice.customer_id)

        items = session.exec(
            select(InvoiceItem).where(
                InvoiceItem.invoice_id == invoice.id
            )
        ).all()

        return templates.TemplateResponse(
            request=request,
            name="payflow/invoice_print.html",
            context={
                "invoice": invoice,
                "customer": customer,
                "items": items,
            },
        )
