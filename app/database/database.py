from sqlmodel import SQLModel, Session, create_engine

from app.config.settings import settings


engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    """Create all registered database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Provide a database session to FastAPI routes."""
    with Session(engine) as session:
        yield session