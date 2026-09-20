from sqlmodel import Session

from app.database.database import engine
from app.models.automation import (
    AutomationRule,
    AutomationRun,
)
from app.services.automation import (
    create_rule,
    execute_rule,
    get_run_history,
    get_rules,
    toggle_rule,
)


def test_create_manual_automation_rule():
    with Session(engine) as session:

        rule = create_rule(
            session=session,
            name="Test automation",
            description="Testing automation creation.",
            trigger_type="manual",
            interval_minutes=None,
            action_type="clean_latest",
        )

        assert rule.id is not None
        assert rule.name == "Test automation"
        assert rule.trigger_type == "manual"
        assert rule.action_type == "clean_latest"
        assert rule.active is True


def test_create_interval_automation_rule():
    with Session(engine) as session:

        rule = create_rule(
            session=session,
            name="Scheduled cleaning",
            description=None,
            trigger_type="interval",
            interval_minutes=60,
            action_type="clean_latest",
        )

        assert rule.id is not None
        assert rule.trigger_type == "interval"
        assert rule.interval_minutes == 60
        assert rule.next_run is not None


def test_invalid_interval_is_rejected():
    with Session(engine) as session:

        try:
            create_rule(
                session=session,
                name="Invalid automation",
                description=None,
                trigger_type="interval",
                interval_minutes=0,
                action_type="clean_latest",
            )

            assert False

        except ValueError as exc:
            assert "at least 1 minute" in str(exc)


def test_toggle_automation():
    with Session(engine) as session:

        rule = create_rule(
            session=session,
            name="Toggle test",
            description=None,
            trigger_type="interval",
            interval_minutes=30,
            action_type="clean_latest",
        )

        assert rule.active is True

        toggle_rule(
            session,
            rule,
        )

        session.refresh(rule)

        assert rule.active is False

        toggle_rule(
            session,
            rule,
        )

        session.refresh(rule)

        assert rule.active is True
        assert rule.next_run is not None


def test_manual_automation_run_is_recorded():
    with Session(engine) as session:

        rule = create_rule(
            session=session,
            name="Run test",
            description=None,
            trigger_type="manual",
            interval_minutes=None,
            action_type="clean_latest",
        )

        run = execute_rule(
            session=session,
            rule=rule,
        )

        assert run.id is not None
        assert run.rule_id == rule.id
        assert run.status in {"success", "failed"}
        assert run.completed_at is not None
        assert run.message


def test_run_history_returns_runs():
    with Session(engine) as session:

        history = get_run_history(
            session=session,
        )

        assert isinstance(history, list)


def test_get_rules_returns_rules():
    with Session(engine) as session:

        rules = get_rules(
            session=session,
        )

        assert isinstance(rules, list)
        assert len(rules) >= 1


def test_automation_models_exist():
    assert AutomationRule.__tablename__ == "automationrule"
    assert AutomationRun.__tablename__ == "automationrun"