from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.sla import breaches, sla_status
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
def test_due_times_match_documented_priority_targets(priority, response, resolution):
    status = sla_status(make_incident(priority=priority, opened_at=OPENED), OPENED)

    assert status.response_due == OPENED + response
    assert status.resolution_due == OPENED + resolution


@pytest.mark.parametrize(
    ("field", "target"),
    [("acknowledged_at", "response"), ("resolved_at", "resolution")],
)
def test_completed_target_is_met_when_completed_before_due(field, target):
    incident = make_incident(opened_at=OPENED)
    due = OPENED + timedelta(minutes=30) if target == "response" else OPENED + timedelta(hours=8)
    setattr(incident, field, due - timedelta(seconds=1))

    status = sla_status(incident, due + timedelta(days=1))

    assert not getattr(status, f"{target}_breached")


@pytest.mark.parametrize(
    ("field", "target"),
    [("acknowledged_at", "response"), ("resolved_at", "resolution")],
)
def test_completed_target_is_breached_when_completed_after_due(field, target):
    incident = make_incident(opened_at=OPENED)
    due = OPENED + timedelta(minutes=30) if target == "response" else OPENED + timedelta(hours=8)
    setattr(incident, field, due + timedelta(seconds=1))

    status = sla_status(incident, OPENED)

    assert getattr(status, f"{target}_breached")


@pytest.mark.parametrize(
    ("field", "target"),
    [("acknowledged_at", "response"), ("resolved_at", "resolution")],
)
@pytest.mark.xfail(reason="SLA comparisons currently treat completion exactly at the due time as on time")
def test_completed_target_at_due_time_is_breached(field, target):
    incident = make_incident(opened_at=OPENED)
    due = OPENED + timedelta(minutes=30) if target == "response" else OPENED + timedelta(hours=8)
    setattr(incident, field, due)

    status = sla_status(incident, OPENED)

    assert getattr(status, f"{target}_breached")


def test_open_incident_is_breached_after_due_times_pass():
    incident = make_incident(opened_at=OPENED)

    status = sla_status(incident, OPENED + timedelta(days=1))

    assert status.response_breached
    assert status.resolution_breached


def test_accumulated_customer_waiting_time_moves_resolution_due_time():
    incident = make_incident(opened_at=OPENED, waiting_seconds=900)

    status = sla_status(incident, OPENED)

    assert status.resolution_due == OPENED + timedelta(hours=8, minutes=15)


def test_current_customer_waiting_time_moves_resolution_due_time():
    waiting_since = OPENED + timedelta(hours=1)
    now = waiting_since + timedelta(minutes=20)
    incident = make_incident(status="waiting", opened_at=OPENED, waiting_since=waiting_since)

    status = sla_status(incident, now)

    assert status.resolution_due == OPENED + timedelta(hours=8, minutes=20)


def test_customer_waiting_does_not_pause_response_target():
    waiting_since = OPENED + timedelta(minutes=10)
    now = OPENED + timedelta(minutes=31)
    incident = make_incident(status="waiting", opened_at=OPENED, waiting_since=waiting_since)

    status = sla_status(incident, now)

    assert status.response_breached
    assert not status.resolution_breached


def test_breaches_reports_each_breached_target_once():
    incident = make_incident(key="INC-1", opened_at=OPENED)

    assert breaches([incident], OPENED + timedelta(days=1)) == [
        ("INC-1", "response"),
        ("INC-1", "resolution"),
    ]
