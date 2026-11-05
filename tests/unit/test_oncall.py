from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from incidentdesk.oncall.handoff import handoff_note
from incidentdesk.oncall.rotation import shifts
from incidentdesk.oncall.schedule import on_call
from tests.conftest import chicago, make_incident, make_service


def test_handoff_happens_monday_at_ten_local():
    before = chicago(2026, 10, 12, 9, 59)
    after = chicago(2026, 10, 12, 10, 0)
    assert on_call("amer", before) != on_call("amer", after)


def test_each_rotation_uses_its_own_time_zone():
    lisbon = ZoneInfo("Europe/Lisbon")
    at = datetime(2026, 10, 12, 10, 30, tzinfo=lisbon)
    assert on_call("emea", at) != on_call("emea", datetime(2026, 10, 12, 9, 30, tzinfo=lisbon))


def test_shift_table_keeps_ten_oclock_across_daylight_saving():
    table = shifts("amer", chicago(2026, 10, 27, 12, 0), weeks=2)
    tz = ZoneInfo("America/Chicago")
    assert [s.starts_at.astimezone(tz).hour for s in table] == [10, 10]
    assert table[0].ends_at == table[1].starts_at


def test_handoff_note_empty_open_incidents():
    assert handoff_note("amer", chicago(2026, 10, 12, 10, 0), []) == (
        "Handoff amer - Mon 12 Oct 10:00 CDT\n"
        "No open incidents."
    )


def test_handoff_note_sorts_by_priority_then_opened_at():
    incidents = [
        make_incident(key="INC-4823", priority="P2", opened_at=chicago(2026, 10, 13, 14, 0), title="Third"),
        make_incident(key="INC-4822", priority="P1", opened_at=chicago(2026, 10, 13, 15, 0), title="Second"),
        make_incident(key="INC-4824", priority="P1", opened_at=chicago(2026, 10, 13, 13, 0), title="First"),
    ]

    assert handoff_note("amer", chicago(2026, 10, 13, 16, 0), incidents) == (
        "Handoff amer - Tue 13 Oct 16:00 CDT\n"
        "- INC-4824 P1 First (open since Tue 13:00)\n"
        "- INC-4822 P1 Second (open since Tue 15:00)\n"
        "- INC-4823 P2 Third (open since Tue 14:00)"
    )


@pytest.mark.parametrize(
    ("at", "opened_at", "expected"),
    [
        (
            datetime(2026, 10, 31, 16, 0, tzinfo=ZoneInfo("UTC")),
            datetime(2026, 10, 31, 14, 15, tzinfo=ZoneInfo("UTC")),
            "Handoff amer - Sat 31 Oct 11:00 CDT\n"
            "- INC-4821 P2 Login fails for some customers (open since Sat 09:15)",
        ),
        (
            datetime(2026, 11, 2, 16, 0, tzinfo=ZoneInfo("UTC")),
            datetime(2026, 11, 2, 15, 30, tzinfo=ZoneInfo("UTC")),
            "Handoff amer - Mon 02 Nov 10:00 CST\n"
            "- INC-4821 P2 Login fails for some customers (open since Mon 09:30)",
        ),
    ],
)
def test_handoff_note_uses_rotation_timezone_before_and_after_dst(at, opened_at, expected):
    assert handoff_note("amer", at, [make_incident(opened_at=opened_at)]) == expected


def test_handoff_note_excludes_resolved_and_other_rotation_incidents():
    incidents = [
        make_incident(key="INC-4822", status="resolved"),
        make_incident(key="INC-4823", service=make_service(rotation="emea")),
    ]

    assert handoff_note("amer", chicago(2026, 10, 12, 10, 0), incidents) == (
        "Handoff amer - Mon 12 Oct 10:00 CDT\n"
        "No open incidents."
    )
