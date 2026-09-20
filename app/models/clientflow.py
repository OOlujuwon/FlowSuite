from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FollowUp(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    customer_id: int = Field(
        foreign_key="customer.id",
        index=True,
    )

    title: str
    description: Optional[str] = None

    due_date: date = Field(index=True)

    status: str = Field(
        default="pending",
        index=True,
    )

    completed_at: Optional[datetime] = None

    created_at: datetime = Field(
        default_factory=utc_now,
    )


class CustomerStatus:
    ACTIVE = "active"
    LEAD = "lead"
    INACTIVE = "inactive"

    ALL = (
        ACTIVE,
        LEAD,
        INACTIVE,
    )


class FollowUpStatus:
    PENDING = "pending"
    COMPLETED = "completed"

    ALL = (
        PENDING,
        COMPLETED,
    )