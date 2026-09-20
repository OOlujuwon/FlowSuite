from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AutomationRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    description: Optional[str] = None

    trigger_type: str = Field(
        default="manual",
        index=True,
    )

    interval_minutes: Optional[int] = None

    action_type: str = Field(
        default="clean_latest",
        index=True,
    )

    active: bool = Field(
        default=True,
        index=True,
    )

    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )


class AutomationRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    rule_id: int = Field(
        foreign_key="automationrule.id",
        index=True,
    )

    started_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    completed_at: Optional[datetime] = None

    status: str = Field(
        default="running",
        index=True,
    )

    message: str = ""