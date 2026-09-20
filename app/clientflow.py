from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database.database import get_session
from app.models.clientflow import CustomerStatus, FollowUpStatus
from app.services.clientflow import (
    complete_followup,
    create_customer,
    create_followup,
    customer_activities,
    dashboard_stats,
    delete_customer,
    get_customer,
    list_customers,
    list_followups,
    update_customer,
)

router = APIRouter(
    prefix="/clientflow",
)

templates = Jinja2Templates(
    directory="templates"
)


@router.get(
    "",
    response_class=HTMLResponse,
)
def dashboard(
    request: Request,
    session: Session = Depends(get_session),
):
    stats = dashboard_stats(session)

    followups = list_followups(
        session=session,
        status=FollowUpStatus.PENDING,
    )[:10]

    customers = list_customers(session=session)[:10]

    return templates.TemplateResponse(
        request=request,
        name="clientflow/dashboard.html",
        context={
            "request": request,
            "stats": stats,
            "followups": followups,
            "customers": customers,
        },
    )


@router.get(
    "/customers",
    response_class=HTMLResponse,
)
def customers(
    request: Request,
    search: str | None = None,
    status: str | None = None,
    session: Session = Depends(get_session),
):
    customer_list = list_customers(
        session=session,
        search=search,
        status=status,
    )

    return templates.TemplateResponse(
        request=request,
        name="clientflow/customers.html",
        context={
            "request": request,
            "customers": customer_list,
            "search": search or "",
            "selected_status": status or "",
            "statuses": CustomerStatus.ALL,
        },
    )


@router.get(
    "/customers/new",
    response_class=HTMLResponse,
)
def new_customer_form(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="clientflow/customer_form.html",
        context={
            "request": request,
            "customer": None,
            "statuses": CustomerStatus.ALL,
        },
    )


@router.post(
    "/customers/new",
)
def create_customer_route(
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    company: str = Form(""),
    status: str = Form(CustomerStatus.LEAD),
    notes: str = Form(""),
    session: Session = Depends(get_session),
):
    try:
        create_customer(
            session=session,
            name=name,
            email=email,
            phone=phone,
            company=company,
            status=status,
            notes=notes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return RedirectResponse(
        url="/clientflow/customers",
        status_code=303,
    )


@router.get(
    "/customers/{customer_id}",
    response_class=HTMLResponse,
)
def customer_detail(
    request: Request,
    customer_id: int,
    session: Session = Depends(get_session),
):
    customer = get_customer(
        session,
        customer_id,
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    followups = list_followups(
        session=session,
        customer_id=customer_id,
    )

    activities = customer_activities(
        session=session,
        customer_id=customer_id,
    )

    return templates.TemplateResponse(
        request=request,
        name="clientflow/customer_detail.html",
        context={
            "request": request,
            "customer": customer,
            "followups": followups,
            "activities": activities,
        },
    )


@router.get(
    "/customers/{customer_id}/edit",
    response_class=HTMLResponse,
)
def edit_customer_form(
    request: Request,
    customer_id: int,
    session: Session = Depends(get_session),
):
    customer = get_customer(
        session,
        customer_id,
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    return templates.TemplateResponse(
        request=request,
        name="clientflow/customer_form.html",
        context={
            "request": request,
            "customer": customer,
            "statuses": CustomerStatus.ALL,
        },
    )


@router.post(
    "/customers/{customer_id}/edit",
)
def update_customer_route(
    customer_id: int,
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    company: str = Form(""),
    status: str = Form(CustomerStatus.LEAD),
    notes: str = Form(""),
    session: Session = Depends(get_session),
):
    customer = get_customer(
        session,
        customer_id,
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    try:
        update_customer(
            session=session,
            customer=customer,
            name=name,
            email=email,
            phone=phone,
            company=company,
            status=status,
            notes=notes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return RedirectResponse(
        url=f"/clientflow/customers/{customer_id}",
        status_code=303,
    )


@router.post(
    "/customers/{customer_id}/delete",
)
def delete_customer_route(
    customer_id: int,
    session: Session = Depends(get_session),
):
    customer = get_customer(
        session,
        customer_id,
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    delete_customer(
        session=session,
        customer=customer,
    )

    return RedirectResponse(
        url="/clientflow/customers",
        status_code=303,
    )


@router.post(
    "/customers/{customer_id}/followups",
)
def create_followup_route(
    customer_id: int,
    title: str = Form(...),
    due_date: date = Form(...),
    description: str = Form(""),
    session: Session = Depends(get_session),
):
    try:
        create_followup(
            session=session,
            customer_id=customer_id,
            title=title,
            due_date=due_date,
            description=description,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return RedirectResponse(
        url=f"/clientflow/customers/{customer_id}",
        status_code=303,
    )


@router.post(
    "/followups/{followup_id}/complete",
)
def complete_followup_route(
    followup_id: int,
    session: Session = Depends(get_session),
):
    followups = list_followups(session=session)

    followup = next(
        (
            item
            for item in followups
            if item.id == followup_id
        ),
        None,
    )

    if not followup:
        raise HTTPException(
            status_code=404,
            detail="Follow-up not found.",
        )

    complete_followup(
        session=session,
        followup=followup,
    )

    return RedirectResponse(
        url="/clientflow",
        status_code=303,
    )