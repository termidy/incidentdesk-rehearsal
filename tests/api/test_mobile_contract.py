from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.models import Incident, Service

pytestmark = pytest.mark.db


def test_mobile_incident_list_matches_response_example(client, db):
    service = Service(slug="login-service", name="Login Service", team="identity", rotation="amer")
    opened_at = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    db.add(service)
    db.flush()
    db.add_all(
        [
            Incident(
                key="INC-4821",
                title="Login fails for some customers",
                service=service,
                severity="major",
                priority="P1",
                status="acknowledged",
                opened_at=opened_at,
            ),
            Incident(
                key="INC-4822",
                title="Login fails for some customers",
                service=service,
                severity="major",
                priority="P1",
                status="open",
                opened_at=opened_at + timedelta(minutes=1),
            ),
            Incident(
                key="INC-4823",
                title="Login fails for some customers",
                service=service,
                severity="major",
                priority="P1",
                status="resolved",
                opened_at=opened_at + timedelta(minutes=2),
            ),
        ]
    )
    db.commit()

    response = client.get("/mobile/v1/incidents")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "key": "INC-4822",
                "title": "Login fails for some customers",
                "service": "login-service",
                "priority": "P1",
                "status": "open",
                "opened_at": "2026-10-13T19:01:00Z",
            },
            {
                "key": "INC-4821",
                "title": "Login fails for some customers",
                "service": "login-service",
                "priority": "P1",
                "status": "acknowledged",
                "opened_at": "2026-10-13T19:00:00Z",
            },
        ],
        "next_page": None,
    }
