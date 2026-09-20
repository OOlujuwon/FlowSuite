from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.clientflow import router as clientflow_router
from app.payflow import router as payflow_router
from app.config.settings import settings
from app.database.database import create_db_and_tables
from app.services.pricing import (
    cleanflow_file_price,
    currency_symbol,
)
from app.shared.errors import (
    FlowSuiteError,
    flowsuite_error_handler,
)


templates = Jinja2Templates(
    directory="templates"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    create_db_and_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "FlowSuite — simple self-service "
        "business operations tools."
    ),
    lifespan=lifespan,
)


app.add_exception_handler(
    FlowSuiteError,
    flowsuite_error_handler,
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


app.include_router(
    clientflow_router,
)

app.include_router(
    payflow_router,
)


@app.get(
    "/",
    response_class=HTMLResponse,
)
def home(request: Request):
    context = {
        "request": request,
        "app_name": settings.app_name,
        "version": settings.app_version,
    }

    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context=context,
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/pricing/cleanflow")
def cleanflow_pricing(
    quantity: int = 1,
    currency: str = "NGN",
):
    total = cleanflow_file_price(
        quantity,
        currency,
    )

    return {
        "service": "CleanFlow",
        "unit": "file",
        "quantity": quantity,
        "currency": currency.upper(),
        "symbol": currency_symbol(currency),
        "total": str(total),
    }