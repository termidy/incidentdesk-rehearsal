from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.sla import RESOLUTION, RESPONSE, breaches, sla_status, waiting_time
from tests.conftest import make_incident


OPENED = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("priority", "response", "resolution"),
    [
        ("P1", timedelta(minutes=15), timedelta(hours=4)),
        ("P2", timedelta(minutes=30), timedelta(hours=8)),
        ("P3", timedelta(hours=4), timedelta(days=3)),
        ("P4", timedelta(days=1), timedelta(days=10)),
    ],
)
def test_sla_deadlines_are_measured_from_opened_at(priority, response, resolution):
    status = sla_status(make_incident(priority=priority, opened_at=OPENED), OPENED)

    assert status.response_due == OPENED + response
    assert status.resolution_due == OPENED + resolution


@pytest.mark.parametrize(
    ("priority", "field", "target"),
    [
        ("P1", "acknowledged_at", "response"),
        ("P1", "resolved_at", "resolution"),
    ],
)
def test_recorded_target_is_met_at_due_time_and_breached_after(priority, field, target):
    due = OPENED + (RESPONSE[priority] if target == "response" else RESOLUTION[priority])
    now = due + timedelta(days=1)

    at_due = make_incident(priority=priority, opened_at=OPENED, **{field: due})
    after_due = make_incident(
        priority=priority,
        opened_at=OPENED,
        **{field: due + timedelta(microseconds=1)},
    )

    assert getattr(sla_status(at_due, now), f"{target}_breached") is False
    assert getattr(sla_status(after_due, now), f"{target}_breached") is True


def test_open_incident_breaches_when_each_due_time_has_passed():
    incident = make_incident(priority="P1", opened_at=OPENED)

    at_response_due = sla_status(incident, OPENED + RESPONSE["P1"])
    at_resolution_due = sla_status(incident, OPENED + RESOLUTION["P1"])
    after_resolution_due = sla_status(
        incident,
        OPENED + RESOLUTION["P1"] + timedelta(microseconds=1),
    )

    assert at_response_due.response_breached is False
    assert at_resolution_due.response_breached is True
    assert at_resolution_due.resolution_breached is False
    assert after_resolution_due.response_breached is True
    assert after_resolution_due.resolution_breached is True


def test_waiting_time_includes_completed_and_current_customer_wait():
    incident = make_incident(
        status="waiting",
        opened_at=OPENED,
        waiting_seconds=30 * 60,
        waiting_since=OPENED + timedelta(hours=2),
    )

    assert waiting_time(incident, OPENED + timedelta(hours=3)) == timedelta(hours=1, minutes=30)


def test_customer_wait_extends_resolution_due_but_does_not_pause_response():
    incident = make_incident(
        priority="P1",
        status="waiting",
        opened_at=OPENED,
        waiting_seconds=30 * 60,
        waiting_since=OPENED + timedelta(hours=2),
    )

    status = sla_status(incident, OPENED + timedelta(hours=3))

    assert status.response_due == OPENED + RESPONSE["P1"]
    assert status.response_breached is True
    assert status.resolution_due == OPENED + RESOLUTION["P1"] + timedelta(hours=1, minutes=30)
    assert status.resolution_breached is False


def test_breaches_reports_each_breached_target_once():
    incident = make_incident(priority="P1", opened_at=OPENED)
    now = OPENED + RESOLUTION["P1"] + timedelta(minutes=1)

    assert breaches([incident], now) == [
        (incident.key, "response"),
        (incident.key, "resolution"),
    ]
