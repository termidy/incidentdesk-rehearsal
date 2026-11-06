from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.models import Incident, Service

pytestmark = pytest.mark.db


@pytest.fixture
def login(db):
    service = Service(slug="login-service", name="Login Service", team="identity", rotation="amer")
    db.add(service)
    db.commit()
    return service


def add_incident(db, service, key, opened_at, status="open"):
    db.add(
        Incident(
            key=key,
            title="Login fails for some customers",
            service=service,
            severity="major",
            priority="P1",
            status=status,
            opened_at=opened_at,
        )
    )
    db.commit()


def test_mobile_incidents_match_list_contract_example(client, db, login):
    opened_at = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    add_incident(db, login, "INC-4821", opened_at, "acknowledged")
    for index in range(1, 21):
        add_incident(
            db,
            login,
            f"INC-{index + 4821}",
            opened_at - timedelta(minutes=index),
        )

    response = client.get("/mobile/v1/incidents")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "next_page"}
    assert body["items"][0] == {
        "key": "INC-4821",
        "title": "Login fails for some customers",
        "service": "login-service",
        "priority": "P1",
        "status": "acknowledged",
        "opened_at": "2026-10-13T19:00:00Z",
    }
    assert body["next_page"] == 2


def test_mobile_incidents_include_fields_and_exclude_resolved(client, db, login):
    opened_at = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    add_incident(db, login, "INC-4821", opened_at, "acknowledged")
    add_incident(db, login, "INC-4822", opened_at + timedelta(minutes=1))
    add_incident(db, login, "INC-4823", opened_at + timedelta(minutes=2), "resolved")

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


def test_mobile_incidents_are_paginated_in_pages_of_20(client, db, login):
    first_opened_at = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    for index in range(21):
        add_incident(
            db,
            login,
            f"INC-{index + 1}",
            first_opened_at + timedelta(minutes=index),
        )

    first_page = client.get("/mobile/v1/incidents").json()
    second_page = client.get("/mobile/v1/incidents", params={"page": 2}).json()

    assert len(first_page["items"]) == 20
    assert first_page["items"][0]["key"] == "INC-21"
    assert first_page["next_page"] == 2
    assert second_page["items"] == [
        {
            "key": "INC-1",
            "title": "Login fails for some customers",
            "service": "login-service",
            "priority": "P1",
            "status": "open",
            "opened_at": "2026-10-13T19:00:00Z",
        }
    ]
    assert second_page["next_page"] is None
