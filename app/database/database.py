from sqlmodel import SQLModel, Session, create_engine

from app.config.settings import settings

from app.models.shared import Customer, Activity, Currency, PricingRule
from app.models.clientflow import FollowUp
from app.models.payflow import Invoice, InvoiceItem, Payment, PaymentReminder
from app.models.automation import (
    AutomationRule,
    AutomationRun,
)


engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
