from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.clientflow import (
    CustomerStatus,
    FollowUp,
    FollowUpStatus,
)
from app.models.shared import Activity, Customer


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_activity(
    session: Session,
    action: str,
    description: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
) -> Activity:
    activity = Activity(
        action=action,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    session.add(activity)
    session.commit()
    session.refresh(activity)

    return activity


def get_customer(
    session: Session,
    customer_id: int,
) -> Optional[Customer]:
    return session.get(Customer, customer_id)


def list_customers(
    session: Session,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> list[Customer]:

    statement = select(Customer).order_by(
        Customer.created_at.desc()
    )

    if search:
        search_term = f"%{search.strip()}%"

        statement = statement.where(
            (
                Customer.name.ilike(search_term)
            )
            | (
                Customer.email.ilike(search_term)
            )
            | (
                Customer.phone.ilike(search_term)
            )
            | (
                Customer.company.ilike(search_term)
            )
        )

    if status and status in CustomerStatus.ALL:
        statement = statement.where(
            Customer.status == status
        )

    return list(session.exec(statement).all())


def create_customer(
    session: Session,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    status: str = CustomerStatus.LEAD,
    notes: Optional[str] = None,
) -> Customer:

    name = name.strip()

    if not name:
        raise ValueError("Customer name is required.")

    if status not in CustomerStatus.ALL:
        raise ValueError("Invalid customer status.")

    customer = Customer(
        name=name,
        email=email.strip() if email else None,
        phone=phone.strip() if phone else None,
        company=company.strip() if company else None,
        status=status,
        notes=notes.strip() if notes else None,
    )

    session.add(customer)
    session.commit()
    session.refresh(customer)

    create_activity(
        session=session,
        action="customer_created",
        description=f"Customer created: {customer.name}",
        entity_type="customer",
        entity_id=customer.id,
    )

    return customer


def update_customer(
    session: Session,
    customer: Customer,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    status: str = CustomerStatus.LEAD,
    notes: Optional[str] = None,
) -> Customer:

    name = name.strip()

    if not name:
        raise ValueError("Customer name is required.")

    if status not in CustomerStatus.ALL:
        raise ValueError("Invalid customer status.")

    customer.name = name
    customer.email = email.strip() if email else None
    customer.phone = phone.strip() if phone else None
    customer.company = company.strip() if company else None
    customer.status = status
    customer.notes = notes.strip() if notes else None
    customer.updated_at = utc_now()

    session.add(customer)
    session.commit()
    session.refresh(customer)

    create_activity(
        session=session,
        action="customer_updated",
        description=f"Customer updated: {customer.name}",
        entity_type="customer",
        entity_id=customer.id,
    )

    return customer


def delete_customer(
    session: Session,
    customer: Customer,
) -> None:

    followups = session.exec(
        select(FollowUp).where(
            FollowUp.customer_id == customer.id
        )
    ).all()

    for followup in followups:
        session.delete(followup)

    customer_name = customer.name
    customer_id = customer.id

    session.delete(customer)
    session.commit()

    create_activity(
        session=session,
        action="customer_deleted",
        description=f"Customer deleted: {customer_name}",
        entity_type="customer",
        entity_id=customer_id,
    )


def create_followup(
    session: Session,
    customer_id: int,
    title: str,
    due_date: date,
    description: Optional[str] = None,
) -> FollowUp:

    customer = session.get(Customer, customer_id)

    if not customer:
        raise ValueError("Customer not found.")

    title = title.strip()

    if not title:
        raise ValueError("Follow-up title is required.")

    followup = FollowUp(
        customer_id=customer_id,
        title=title,
        description=(
            description.strip()
            if description
            else None
        ),
        due_date=due_date,
    )

    session.add(followup)
    session.commit()
    session.refresh(followup)

    create_activity(
        session=session,
        action="followup_created",
        description=(
            f"Follow-up created for {customer.name}: "
            f"{followup.title}"
        ),
        entity_type="customer",
        entity_id=customer_id,
    )

    return followup


def list_followups(
    session: Session,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[FollowUp]:

    statement = select(FollowUp).order_by(
        FollowUp.due_date.asc()
    )

    if customer_id:
        statement = statement.where(
            FollowUp.customer_id == customer_id
        )

    if status and status in FollowUpStatus.ALL:
        statement = statement.where(
            FollowUp.status == status
        )

    return list(session.exec(statement).all())


def complete_followup(
    session: Session,
    followup: FollowUp,
) -> FollowUp:

    followup.status = FollowUpStatus.COMPLETED
    followup.completed_at = utc_now()

    session.add(followup)
    session.commit()
    session.refresh(followup)

    create_activity(
        session=session,
        action="followup_completed",
        description=f"Follow-up completed: {followup.title}",
        entity_type="customer",
        entity_id=followup.customer_id,
    )

    return followup


def customer_activities(
    session: Session,
    customer_id: int,
) -> list[Activity]:

    statement = (
        select(Activity)
        .where(
            Activity.entity_type == "customer",
            Activity.entity_id == customer_id,
        )
        .order_by(Activity.created_at.desc())
    )

    return list(session.exec(statement).all())


def dashboard_stats(
    session: Session,
) -> dict:

    customers = list(
        session.exec(
            select(Customer)
        ).all()
    )

    followups = list(
        session.exec(
            select(FollowUp)
        ).all()
    )

    pending = [
        item
        for item in followups
        if item.status == FollowUpStatus.PENDING
    ]

    overdue = [
        item
        for item in pending
        if item.due_date < date.today()
    ]

    return {
        "customers": len(customers),
        "active_customers": sum(
            1
            for customer in customers
            if customer.status == CustomerStatus.ACTIVE
        ),
        "leads": sum(
            1
            for customer in customers
            if customer.status == CustomerStatus.LEAD
        ),
        "pending_followups": len(pending),
        "overdue_followups": len(overdue),
    }