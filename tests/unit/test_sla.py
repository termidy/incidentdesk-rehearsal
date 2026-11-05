from datetime import timedelta, timezone

import pytest

from incidentdesk.sla import breaches, sla_status
from tests.conftest import chicago, make_incident


@pytest.mark.parametrize(
    ("priority", "response", "resolution"),
    [
        ("P1", timedelta(minutes=15), timedelta(hours=4)),
        ("P2", timedelta(minutes=30), timedelta(hours=8)),
        ("P3", timedelta(hours=4), timedelta(days=3)),
        ("P4", timedelta(days=1), timedelta(days=10)),
    ],
)
def test_due_times_follow_priority_targets(priority, response, resolution):
    opened = chicago(2026, 10, 13, 14, 0)
    status = sla_status(make_incident(priority=priority, opened_at=opened), opened)

    assert status.response_due == opened.astimezone(timezone.utc) + response
    assert status.resolution_due == opened.astimezone(timezone.utc) + resolution
    assert not status.response_breached
    assert not status.resolution_breached


@pytest.mark.xfail(reason="SLA checks use >, but docs/sla.md says targets must be met before the due time")
@pytest.mark.parametrize("target", ["response", "resolution"])
def test_due_time_itself_is_a_breach_per_documented_before_rule(target):
    opened = chicago(2026, 10, 13, 14, 0)
    incident = make_incident(priority="P1", opened_at=opened)
    due = opened + (timedelta(minutes=15) if target == "response" else timedelta(hours=4))
    if target == "response":
        incident.acknowledged_at = due
    else:
        incident.resolved_at = due

    assert getattr(sla_status(incident, due), f"{target}_breached")


def test_open_incident_breaches_after_both_due_times():
    opened = chicago(2026, 10, 13, 14, 0)

    status = sla_status(make_incident(priority="P1", opened_at=opened), opened + timedelta(hours=5))

    assert status.response_breached
    assert status.resolution_breached


@pytest.mark.parametrize(
    ("target", "completion_field", "target_duration"),
    [
        ("response", "acknowledged_at", timedelta(minutes=15)),
        ("resolution", "resolved_at", timedelta(hours=4)),
    ],
)
def test_completion_before_due_time_meets_target(target, completion_field, target_duration):
    opened = chicago(2026, 10, 13, 14, 0)
    incident = make_incident(priority="P1", opened_at=opened)
    setattr(incident, completion_field, opened + target_duration - timedelta(seconds=1))

    assert not getattr(sla_status(incident, opened + target_duration), f"{target}_breached")


@pytest.mark.parametrize(
    ("target", "completion_field", "target_duration"),
    [
        ("response", "acknowledged_at", timedelta(minutes=15)),
        ("resolution", "resolved_at", timedelta(hours=4)),
    ],
)
def test_completion_after_due_time_breaches_target(target, completion_field, target_duration):
    opened = chicago(2026, 10, 13, 14, 0)
    incident = make_incident(priority="P1", opened_at=opened)
    setattr(incident, completion_field, opened + target_duration + timedelta(seconds=1))

    assert getattr(sla_status(incident, opened + target_duration), f"{target}_breached")


def test_customer_wait_extends_resolution_but_not_response_due_time():
    opened = chicago(2026, 10, 13, 14, 0)
    incident = make_incident(
        priority="P1",
        status="waiting",
        opened_at=opened,
        waiting_since=opened + timedelta(hours=2),
        waiting_seconds=3600,
    )

    status = sla_status(incident, opened + timedelta(hours=3))

    assert status.response_due == opened.astimezone(timezone.utc) + timedelta(minutes=15)
    assert status.resolution_due == opened.astimezone(timezone.utc) + timedelta(hours=6)
    assert status.response_breached
    assert not status.resolution_breached


def test_breaches_reports_each_breached_target_once():
    opened = chicago(2026, 10, 13, 14, 0)
    incident = make_incident(key="INC-1", priority="P1", opened_at=opened)

    assert breaches([incident], opened + timedelta(hours=5)) == [
        ("INC-1", "response"),
        ("INC-1", "resolution"),
    ]
