from pathlib import Path
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseModel):
    app_name: str = "FlowSuite"
    app_version: str = "0.1.0"
    database_url: str = f"sqlite:///{DATA_DIR / 'flowsuite.db'}"

    # Supported currencies for the first version.
    supported_currencies: tuple[str, ...] = (
        "NGN",
        "GBP",
        "USD",
        "EUR",
    )

    default_currency: str = "NGN"


settings = Settings()