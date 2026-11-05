"""The daily report: incidents of one calendar day in the service time zone."""

from collections import Counter
from datetime import date, datetime, timedelta, timezone

from incidentdesk.models import Incident
from incidentdesk.timeutil import local_datetime


def day_bounds(day: date) -> tuple[datetime, datetime]:
    """Start and end of a local calendar day, in UTC. A daylight saving day is 23 or 25 hours long."""
    start = local_datetime(day.year, day.month, day.day)
    next_day = day + timedelta(days=1)
    end = local_datetime(next_day.year, next_day.month, next_day.day)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def daily_report(incidents: list[Incident], day: date) -> dict:
    start, end = day_bounds(day)
    today = [i for i in incidents if start <= i.opened_at < end]
    return {
        "day": day.isoformat(),
        "opened": len(today),
        "by_priority": dict(sorted(Counter(i.priority for i in today).items())),
        "still_open": sum(1 for i in today if i.status != "resolved"),
    }
