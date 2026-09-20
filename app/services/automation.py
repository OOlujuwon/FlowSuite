from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.cleanflow import cleaning_jobs
from app.models.automation import (
    AutomationRule,
    AutomationRun,
)
from app.services.cleanflow import clean_dataframe


SUPPORTED_TRIGGERS = {
    "manual",
    "interval",
}

SUPPORTED_ACTIONS = {
    "clean_latest",
}


def create_rule(
    session: Session,
    name: str,
    description: Optional[str],
    trigger_type: str,
    interval_minutes: Optional[int],
    action_type: str,
) -> AutomationRule:
    trigger_type = trigger_type.strip().lower()
    action_type = action_type.strip().lower()

    if trigger_type not in SUPPORTED_TRIGGERS:
        raise ValueError(
            "Unsupported trigger type."
        )

    if action_type not in SUPPORTED_ACTIONS:
        raise ValueError(
            "Unsupported action type."
        )

    if not name.strip():
        raise ValueError(
            "Automation name is required."
        )

    if trigger_type == "interval":
        if not interval_minutes or interval_minutes < 1:
            raise ValueError(
                "Interval must be at least 1 minute."
            )

    else:
        interval_minutes = None

    now = datetime.utcnow()

    next_run = None

    if trigger_type == "interval":
        next_run = now + timedelta(
            minutes=interval_minutes
        )

    rule = AutomationRule(
        name=name.strip(),
        description=description.strip()
        if description
        else None,
        trigger_type=trigger_type,
        interval_minutes=interval_minutes,
        action_type=action_type,
        active=True,
        next_run=next_run,
    )

    session.add(rule)
    session.commit()
    session.refresh(rule)

    return rule


def get_rules(
    session: Session,
) -> list[AutomationRule]:
    return session.exec(
        select(AutomationRule)
        .order_by(AutomationRule.id.desc())
    ).all()


def get_rule(
    session: Session,
    rule_id: int,
) -> Optional[AutomationRule]:
    return session.get(
        AutomationRule,
        rule_id,
    )


def toggle_rule(
    session: Session,
    rule: AutomationRule,
) -> AutomationRule:
    rule.active = not rule.active

    if rule.active and rule.trigger_type == "interval":
        rule.next_run = datetime.utcnow() + timedelta(
            minutes=rule.interval_minutes or 1
        )

    session.add(rule)
    session.commit()
    session.refresh(rule)

    return rule


def run_clean_latest(
    session: Session,
) -> str:
    """
    Run CleanFlow against the most recently uploaded
    CleanFlow job currently held in memory.
    """

    if not cleaning_jobs:
        return (
            "No CleanFlow files are currently available "
            "for automation."
        )

    latest_job_id = next(
        reversed(cleaning_jobs)
    )

    job = cleaning_jobs[latest_job_id]

    cleaned_dataframe, summary = clean_dataframe(
        job["dataframe"]
    )

    job["dataframe"] = cleaned_dataframe
    job["summary"] = summary

    return (
        f"Cleaned latest file: "
        f"{job['original_filename']}. "
        f"{summary['total_changes']} changes recorded."
    )


def execute_rule(
    session: Session,
    rule: AutomationRule,
) -> AutomationRun:
    started_at = datetime.utcnow()

    run = AutomationRun(
        rule_id=rule.id,
        started_at=started_at,
        status="running",
    )

    session.add(run)
    session.commit()
    session.refresh(run)

    try:
        if rule.action_type == "clean_latest":
            message = run_clean_latest(session)

        else:
            raise ValueError(
                f"Unsupported action: {rule.action_type}"
            )

        run.status = "success"
        run.message = message

    except Exception as exc:
        run.status = "failed"
        run.message = str(exc)

    run.completed_at = datetime.utcnow()

    rule.last_run = run.completed_at

    if (
        rule.trigger_type == "interval"
        and rule.interval_minutes
        and rule.active
    ):
        rule.next_run = (
            run.completed_at
            + timedelta(
                minutes=rule.interval_minutes
            )
        )
    else:
        rule.next_run = None

    session.add(run)
    session.add(rule)
    session.commit()
    session.refresh(run)

    return run


def run_due_automations(
    session: Session,
) -> list[AutomationRun]:
    now = datetime.utcnow()

    rules = session.exec(
        select(AutomationRule).where(
            AutomationRule.active == True,
            AutomationRule.trigger_type == "interval",
            AutomationRule.next_run <= now,
        )
    ).all()

    runs = []

    for rule in rules:
        runs.append(
            execute_rule(
                session=session,
                rule=rule,
            )
        )

    return runs


def get_run_history(
    session: Session,
    limit: int = 50,
) -> list[AutomationRun]:
    return session.exec(
        select(AutomationRun)
        .order_by(AutomationRun.id.desc())
        .limit(limit)
    ).all()