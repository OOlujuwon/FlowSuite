from fastapi.testclient import TestClient

from app.main import app
from app.services.pricing import cleanflow_file_price


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["application"] == "FlowSuite"


def test_homepage():
    response = client.get("/")

    assert response.status_code == 200
    assert "FlowSuite" in response.text
    assert "ClientFlow" in response.text
    assert "PayFlow" in response.text
    assert "CleanFlow" in response.text


def test_cleanflow_pricing():
    total = cleanflow_file_price(
        quantity=10,
        currency="NGN",
    )

    assert total == 1000


def test_cleanflow_volume_pricing():
    total = cleanflow_file_price(
        quantity=100,
        currency="NGN",
    )

    assert total == 7000