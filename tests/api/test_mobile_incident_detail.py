from datetime import datetime, timezone

import pytest

from incidentdesk.models import Incident, Service, TimelineEvent

pytestmark = pytest.mark.db


def _utc(hour, minute=0):
    return datetime(2026, 10, 13, hour, minute, tzinfo=timezone.utc)


@pytest.fixture
def incident(db):
    service = Service(slug="login-service", name="Login Service", team="identity", rotation="amer", customer_facing=True)
    item = Incident(key="INC-4821", title="Login fails for some customers", severity="major", priority="P1",
                    status="acknowledged", opened_at=_utc(19), service=service)
    # inserted newest first to prove the endpoint orders the timeline
    item.events.append(TimelineEvent(at=_utc(19, 5), kind="acknowledged", note="On it"))
    item.events.append(TimelineEvent(at=_utc(19), kind="opened", note=""))
    db.add(item)
    db.commit()
    return item


def test_incident_detail_with_timeline_oldest_first(client, incident):
    r = client.get("/mobile/v1/incidents/INC-4821")
    assert r.status_code == 200
    assert r.json() == {
        "key": "INC-4821", "title": "Login fails for some customers", "service": "login-service",
        "priority": "P1", "status": "acknowledged", "opened_at": "2026-10-13T19:00:00Z",
        "timeline": [
            {"at": "2026-10-13T19:00:00Z", "kind": "opened", "note": ""},
            {"at": "2026-10-13T19:05:00Z", "kind": "acknowledged", "note": "On it"},
        ],
    }


def test_unknown_key_is_not_found(client, incident):
    r = client.get("/mobile/v1/incidents/INC-0")
    assert r.status_code == 404
    assert r.json() == {"error": "not_found"}
