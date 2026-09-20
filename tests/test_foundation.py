from datetime import date, timedelta

from fastapi.testclient import TestClient

from fastapi.testclient import TestClient

from app.main import app
from app.database.database import create_db_and_tables
from app.services.pricing import cleanflow_file_price

client = TestClient(app)

create_db_and_tables()

from app.main import app


client = TestClient(app)


def test_clientflow_dashboard():
    response = client.get("/clientflow")

    assert response.status_code == 200
    assert "ClientFlow" in response.text
    assert "Customer dashboard" in response.text


def test_customer_creation():
    response = client.post(
        "/clientflow/customers/new",
        data={
            "name": "Test Customer",
            "email": "test@example.com",
            "phone": "08000000000",
            "company": "Test Company",
            "status": "lead",
            "notes": "Test note",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "/clientflow/customers" in response.headers["location"]


def test_customer_list():
    response = client.get(
        "/clientflow/customers"
    )

    assert response.status_code == 200
    assert "Test Customer" in response.text


def test_customer_search():
    response = client.get(
        "/clientflow/customers?search=Test%20Customer"
    )

    assert response.status_code == 200
    assert "Test Customer" in response.text


def test_customer_detail():
    response = client.get(
        "/clientflow/customers"
    )

    assert response.status_code == 200

    detail_response = client.get(
        "/clientflow/customers/1"
    )

    assert detail_response.status_code == 200


def test_followup_creation():
    response = client.post(
        "/clientflow/customers/1/followups",
        data={
            "title": "Follow up with customer",
            "due_date": str(
                date.today() + timedelta(days=3)
            ),
            "description": "Discuss next order.",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303


def test_followup_completion():
    response = client.post(
        "/clientflow/followups/1/complete",
        follow_redirects=False,
    )

    assert response.status_code == 303