import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_request():
    return {
        "client_name": "Northstar Accounting",
        "project_name": "Business website",
        "project_type": "Web Development",
        "brief": "Build a responsive five-page website with a contact form.",
        "budget_type": "unknown",
        "budget_amount": None,
        "currency": "USD",
        "timeline": "4–6 weeks",
        "freelancer_name": "Alex Morgan Studio",
        "expertise": "Independent web developer",
        "tone": "Professional",
        "constraints": "",
    }
