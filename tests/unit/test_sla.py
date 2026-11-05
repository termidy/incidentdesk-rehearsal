from datetime import timedelta

import pytest

from incidentdesk.sla import RESOLUTION, RESPONSE, breaches, sla_status
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
def test_priority_targets_match_sla_table(priority, response, resolution):
    opened = make_incident(priority=priority).opened_at
    status = sla_status(make_incident(priority=priority), opened)

    assert RESPONSE[priority] == response
    assert RESOLUTION[priority] == resolution
    assert status.response_due == opened + response
    assert status.resolution_due == opened + resolution


@pytest.mark.parametrize("target", ["response", "resolution"])
def test_acknowledgment_or_resolution_at_due_time_meets_target(target):
    incident = make_incident(priority="P1")
    due = incident.opened_at + (RESPONSE["P1"] if target == "response" else RESOLUTION["P1"])
    fields = {"acknowledged_at": due} if target == "response" else {"resolved_at": due}
    incident = make_incident(priority="P1", **fields)

    status = sla_status(incident, due + timedelta(minutes=1))

    assert getattr(status, f"{target}_breached") is False


@pytest.mark.parametrize("target", ["response", "resolution"])
def test_acknowledgment_or_resolution_just_after_due_time_breaches(target):
    opened_incident = make_incident(priority="P1")
    due = opened_incident.opened_at + (
        RESPONSE["P1"] if target == "response" else RESOLUTION["P1"]
    )
    fields = {
        "acknowledged_at": due + timedelta(microseconds=1)
    } if target == "response" else {
        "resolved_at": due + timedelta(microseconds=1)
    }
    incident = make_incident(priority="P1", **fields)

    status = sla_status(incident, due + timedelta(minutes=1))

    assert getattr(status, f"{target}_breached") is True


@pytest.mark.parametrize("target", ["response", "resolution"])
def test_open_incident_breaches_only_after_due_time(target):
    incident = make_incident(priority="P1")
    due = incident.opened_at + (
        RESPONSE["P1"] if target == "response" else RESOLUTION["P1"]
    )

    at_due = sla_status(incident, due)
    just_past_due = sla_status(incident, due + timedelta(microseconds=1))

    assert getattr(at_due, f"{target}_breached") is False
    assert getattr(just_past_due, f"{target}_breached") is True


def test_waiting_extends_resolution_due_by_accumulated_and_ongoing_time_not_response():
    incident = make_incident(
        priority="P1",
        status="waiting",
        waiting_seconds=30 * 60,
    )
    incident.waiting_since = incident.opened_at + timedelta(hours=2)
    now = incident.opened_at + timedelta(hours=3)

    status = sla_status(incident, now)

    assert status.resolution_due == incident.opened_at + timedelta(hours=5, minutes=30)
    assert status.response_due == incident.opened_at + timedelta(minutes=15)
    assert status.response_breached is True
    assert status.resolution_breached is False


def test_breaches_reports_each_breached_target_once():
    opened = make_incident(priority="P1").opened_at
    now = opened + timedelta(days=1)
    incidents = [
        make_incident(key="INC-1001", priority="P1"),
        make_incident(
            key="INC-1002",
            priority="P1",
            acknowledged_at=opened + timedelta(minutes=16),
            resolved_at=opened + timedelta(hours=4, seconds=1),
        ),
    ]

    assert breaches(incidents, now) == [
        ("INC-1001", "response"),
        ("INC-1001", "resolution"),
        ("INC-1002", "response"),
        ("INC-1002", "resolution"),
    ]
