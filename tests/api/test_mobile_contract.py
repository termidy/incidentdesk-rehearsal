from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.models import Incident, Service

pytestmark = pytest.mark.db


def test_mobile_incident_list_matches_issue_41_response_example(client, db):
    service = Service(slug="login-service", name="Login Service", team="identity", rotation="amer")
    db.add(service)
    opened_at = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    for index in range(21):
        db.add(
            Incident(
                key="INC-4821" if index == 0 else f"INC-{index}",
                title="Login fails for some customers",
                service=service,
                severity="major",
                priority="P1",
                status="acknowledged" if index == 0 else "open",
                opened_at=opened_at - timedelta(minutes=index),
            )
        )
    db.commit()

    response = client.get("/mobile/v1/incidents")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items", "next_page"}
    assert payload["items"][0] == {
        "key": "INC-4821",
        "title": "Login fails for some customers",
        "service": "login-service",
        "priority": "P1",
        "status": "acknowledged",
        "opened_at": "2026-10-13T19:00:00Z",
    }
    assert payload["next_page"] == 2
