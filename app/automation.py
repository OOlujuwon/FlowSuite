from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database.database import engine
from app.services.automation import (
    create_rule,
    execute_rule,
    get_rule,
    get_rules,
    get_run_history,
    toggle_rule,
)


router = APIRouter(
    prefix="/automation",
    tags=["Automation"],
)

templates = Jinja2Templates(
    directory="templates"
)


@router.get(
    "/",
    response_class=HTMLResponse,
)
def dashboard(request: Request):
    with Session(engine) as session:
        rules = get_rules(session)
        history = get_run_history(session)

        return templates.TemplateResponse(
            request=request,
            name="automation/dashboard.html",
            context={
                "rules": rules,
                "history": history,
            },
        )


@router.get(
    "/new",
    response_class=HTMLResponse,
)
def new_rule(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="automation/form.html",
        context={},
    )


@router.post("/new")
def create_new_rule(
    name: str = Form(...),
    description: str = Form(""),
    trigger_type: str = Form(...),
    interval_minutes: str = Form(""),
    action_type: str = Form(...),
):
    parsed_interval = None

    if interval_minutes.strip():
        try:
            parsed_interval = int(
                interval_minutes
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Interval must be a whole number.",
            )

    with Session(engine) as session:
        try:
            create_rule(
                session=session,
                name=name,
                description=description,
                trigger_type=trigger_type,
                interval_minutes=parsed_interval,
                action_type=action_type,
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            )

    return RedirectResponse(
        url="/automation/",
        status_code=303,
    )


@router.post(
    "/{rule_id}/toggle"
)
def toggle(
    rule_id: int,
):
    with Session(engine) as session:
        rule = get_rule(
            session,
            rule_id,
        )

        if not rule:
            raise HTTPException(
                status_code=404,
                detail="Automation rule not found.",
            )

        toggle_rule(
            session,
            rule,
        )

    return RedirectResponse(
        url="/automation/",
        status_code=303,
    )


@router.post(
    "/{rule_id}/run"
)
def run_now(
    rule_id: int,
):
    with Session(engine) as session:
        rule = get_rule(
            session,
            rule_id,
        )

        if not rule:
            raise HTTPException(
                status_code=404,
                detail="Automation rule not found.",
            )

        execute_rule(
            session=session,
            rule=rule,
        )

    return RedirectResponse(
        url="/automation/",
        status_code=303,
    )