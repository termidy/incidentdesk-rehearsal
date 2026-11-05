from datetime import timedelta

import pytest

from incidentdesk.sla import breaches, sla_status
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
def test_due_times_for_each_priority(priority, response, resolution):
    incident = make_incident(priority=priority)

    status = sla_status(incident, incident.opened_at)

    assert status.response_due == incident.opened_at + response
    assert status.resolution_due == incident.opened_at + resolution


def test_acknowledgement_and_resolution_at_due_time_are_met():
    incident = make_incident(priority="P1")
    response_due = incident.opened_at + timedelta(minutes=15)
    resolution_due = incident.opened_at + timedelta(hours=4)
    incident.acknowledged_at = response_due
    incident.resolved_at = resolution_due

    status = sla_status(incident, resolution_due)

    assert not status.response_breached
    assert not status.resolution_breached


def test_late_acknowledgement_and_resolution_are_breaches():
    incident = make_incident(priority="P1")
    incident.acknowledged_at = incident.opened_at + timedelta(minutes=15, seconds=1)
    incident.resolved_at = incident.opened_at + timedelta(hours=4, seconds=1)

    status = sla_status(incident, incident.resolved_at)

    assert status.response_breached
    assert status.resolution_breached


def test_open_incident_breaches_after_due_times_pass():
    incident = make_incident(priority="P1")
    now = incident.opened_at + timedelta(hours=4, seconds=1)

    status = sla_status(incident, now)

    assert status.response_breached
    assert status.resolution_breached


def test_customer_wait_extends_only_the_resolution_due_time():
    incident = make_incident(
        priority="P1",
        status="waiting",
        waiting_seconds=600,
    )
    incident.waiting_since = incident.opened_at + timedelta(hours=2)
    now = incident.opened_at + timedelta(hours=3)

    status = sla_status(incident, now)

    assert status.response_due == incident.opened_at + timedelta(minutes=15)
    assert status.resolution_due == incident.opened_at + timedelta(hours=5, minutes=10)
    assert status.response_breached
    assert not status.resolution_breached


def test_ongoing_customer_wait_keeps_extending_resolution_due_time():
    incident = make_incident(
        priority="P1",
        status="waiting",
    )
    incident.waiting_since = incident.opened_at + timedelta(hours=2)
    first_now = incident.opened_at + timedelta(hours=3)
    second_now = first_now + timedelta(hours=1)

    first_status = sla_status(incident, first_now)
    second_status = sla_status(incident, second_now)

    assert second_status.resolution_due - first_status.resolution_due == timedelta(hours=1)
    assert first_status.response_due == second_status.response_due
    assert not first_status.resolution_breached
    assert not second_status.resolution_breached


def test_breaches_reports_each_breached_target_once():
    incident = make_incident(priority="P1")
    now = incident.opened_at + timedelta(hours=4, seconds=1)

    assert breaches([incident], now) == [
        (incident.key, "response"),
        (incident.key, "resolution"),
    ]
