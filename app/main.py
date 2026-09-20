import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.automation import router as automation_router
from app.cleanflow import router as cleanflow_router
from app.clientflow import router as clientflow_router
from app.payflow import router as payflow_router

from app.database.database import (
    create_db_and_tables,
    engine,
)

from app.services.automation import run_due_automations
from app.services.pricing import (
    cleanflow_file_price,
    currency_symbol,
)

from app.shared.errors import (
    FlowSuiteError,
    flowsuite_error_handler,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("flowsuite")

templates = Jinja2Templates(
    directory="templates"
)


async def automation_loop():
    """
    Run scheduled automation rules periodically.

    The loop intentionally runs in the application process
    for the MVP. A production deployment can later move
    scheduled jobs to a dedicated worker.
    """

    while True:
        try:
            with Session(engine) as session:
                run_due_automations(session)

        except Exception:
            logger.exception(
                "Scheduled automation cycle failed."
            )

        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.
    """

    logger.info("Starting FlowSuite.")

    create_db_and_tables()

    scheduler_task = asyncio.create_task(
        automation_loop()
    )

    try:
        yield

    finally:
        logger.info("Stopping FlowSuite.")

        scheduler_task.cancel()

        try:
            await scheduler_task

        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="FlowSuite",
    description=(
        "Small-business revenue operations tools: "
        "ClientFlow, PayFlow and CleanFlow."
    ),
    version="1.0.0",
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


@app.get(
    "/",
    response_class=HTMLResponse,
)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "cleanflow_file_price": cleanflow_file_price,
            "currency_symbol": currency_symbol,
        },
    )


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "FlowSuite",
        "version": "1.0.0",
    }


app.include_router(
    clientflow_router
)

app.include_router(
    payflow_router
)

app.include_router(
    cleanflow_router
)

app.include_router(
    automation_router
)