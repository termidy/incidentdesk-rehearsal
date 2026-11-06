from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.sla import RESPONSE, RESOLUTION, breaches, sla_status, waiting_time
from tests.conftest import make_incident


@pytest.mark.parametrize(
    ("priority", "response", "resolution"),
    [
        ("P1", timedelta(minutes=15), timedelta(hours=4)),
        ("P2", timedelta(minutes=30), timedelta(hours=8)),
        ("P3", timedelta(hours=4), timedelta(days=3)),
        ("P4", timedelta(days=1), timedelta(days=10)),
    ],
)
def test_due_times_match_priority_targets(priority, response, resolution):
    opened = datetime(2026, 1, 1, tzinfo=timezone.utc)
    incident = make_incident(priority=priority, opened_at=opened)

    status = sla_status(incident, opened)

    assert status.response_due == opened + response == opened + RESPONSE[priority]
    assert status.resolution_due == opened + resolution == opened + RESOLUTION[priority]


def test_acknowledgement_and_resolution_at_due_time_meet_targets():
    opened = datetime(2026, 1, 1, tzinfo=timezone.utc)
    incident = make_incident(
        priority="P1",
        opened_at=opened,
        acknowledged_at=opened + timedelta(minutes=15),
        resolved_at=opened + timedelta(hours=4),
    )

    status = sla_status(incident, opened + timedelta(hours=4))

    assert not status.response_breached
    assert not status.resolution_breached


def test_acknowledgement_and_resolution_after_due_time_breach_targets():
    opened = datetime(2026, 1, 1, tzinfo=timezone.utc)
    incident = make_incident(
        priority="P1",
        opened_at=opened,
        acknowledged_at=opened + timedelta(minutes=15, seconds=1),
        resolved_at=opened + timedelta(hours=4, seconds=1),
    )

    status = sla_status(incident, opened + timedelta(days=1))

    assert status.response_breached
    assert status.resolution_breached


def test_waiting_time_includes_completed_and_current_wait():
    opened = datetime(2026, 1, 1, tzinfo=timezone.utc)
    now = opened + timedelta(hours=3)
    incident = make_incident(
        priority="P1",
        status="waiting",
        opened_at=opened,
        waiting_seconds=3600,
        waiting_since=opened + timedelta(hours=1),
    )

    assert waiting_time(incident, now) == timedelta(hours=3)

    status = sla_status(incident, now)
    assert status.response_due == opened + timedelta(minutes=15)
    assert status.resolution_due == opened + timedelta(hours=7)
    assert status.response_breached
    assert not status.resolution_breached


def test_waiting_time_is_not_extended_after_incident_leaves_waiting():
    opened = datetime(2026, 1, 1, tzinfo=timezone.utc)
    now = opened + timedelta(hours=3)
    incident = make_incident(
        priority="P1",
        status="open",
        opened_at=opened,
        waiting_seconds=3600,
        waiting_since=opened + timedelta(hours=1),
    )

    assert waiting_time(incident, now) == timedelta(hours=1)
    assert sla_status(incident, now).resolution_due == opened + timedelta(hours=5)


def test_open_incident_breaches_when_due_time_passes():
    opened = datetime(2026, 1, 1, tzinfo=timezone.utc)
    incident = make_incident(priority="P1", status="open", opened_at=opened)

    status = sla_status(incident, opened + timedelta(hours=5))

    assert status.response_breached
    assert status.resolution_breached


def test_breaches_reports_each_breached_target_once():
    opened = datetime(2026, 1, 1, tzinfo=timezone.utc)
    incident = make_incident(priority="P1", opened_at=opened)

    assert breaches([incident], opened + timedelta(hours=5)) == [
        (incident.key, "response"),
        (incident.key, "resolution"),
    ]
