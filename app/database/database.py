from sqlmodel import SQLModel, Session, create_engine

from app.config.settings import settings

# Import models so SQLModel knows about every table before
# create_all() is called.
from app.models.shared import Customer, Activity, Currency, PricingRule
from app.models.clientflow import FollowUp


engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    """Create all registered FlowSuite database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session