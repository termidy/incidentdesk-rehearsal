from datetime import datetime

import pytz
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
    lisbon = pytz.timezone("Europe/Lisbon")
    at = lisbon.localize(datetime(2026, 10, 12, 10, 30))
    assert on_call("emea", at) != on_call("emea", lisbon.localize(datetime(2026, 10, 12, 9, 30)))


def test_shift_table_keeps_ten_oclock_across_daylight_saving():
    table = shifts("amer", chicago(2026, 10, 27, 12, 0), weeks=2)
    tz = pytz.timezone("America/Chicago")
    assert [s.starts_at.astimezone(tz).hour for s in table] == [10, 10]
    assert table[0].ends_at == table[1].starts_at


def test_handoff_note_lists_open_incidents_of_the_rotation():
    incidents = [
        make_incident(key="INC-4821"),
        make_incident(key="INC-4822", status="resolved"),
        make_incident(key="INC-4823", service=make_service(rotation="emea")),
    ]
    note = handoff_note("amer", chicago(2026, 10, 12, 10, 0), incidents)

    assert "INC-4821" in note
    assert "INC-4822" not in note
    assert "INC-4823" not in note


def test_handoff_note_says_when_there_are_no_open_incidents():
    note = handoff_note("amer", chicago(2026, 10, 13, 14, 0), [])

    assert note == "Handoff amer - Tue 13 Oct 14:00 CDT\nNo open incidents."


def test_handoff_note_sorts_by_priority_then_open_time():
    incidents = [
        make_incident(key="INC-P2-NEW", priority="P2", opened_at=pytz.UTC.localize(datetime(2026, 10, 13, 14))),
        make_incident(key="INC-P1-NEW", priority="P1", opened_at=pytz.UTC.localize(datetime(2026, 10, 13, 13))),
        make_incident(key="INC-P2-OLD", priority="P2", opened_at=pytz.UTC.localize(datetime(2026, 10, 13, 10))),
        make_incident(key="INC-P1-OLD", priority="P1", opened_at=pytz.UTC.localize(datetime(2026, 10, 13, 9))),
    ]
    note = handoff_note("amer", chicago(2026, 10, 13, 14, 0), incidents)

    assert [line.split()[1] for line in note.splitlines()[1:]] == [
        "INC-P1-OLD",
        "INC-P1-NEW",
        "INC-P2-OLD",
        "INC-P2-NEW",
    ]


@pytest.mark.parametrize(
    ("at", "opened_at", "expected_header", "expected_opened"),
    [
        (datetime(2026, 10, 24, 11), datetime(2026, 10, 24, 10, 30), "Sat 24 Oct 12:00 WEST", "Sat 11:30"),
        (datetime(2026, 10, 26, 11), datetime(2026, 10, 26, 10, 30), "Mon 26 Oct 11:00 WET", "Mon 10:30"),
    ],
)
def test_handoff_note_uses_rotation_time_zone_across_dst(at, opened_at, expected_header, expected_opened):
    note = handoff_note(
        "emea",
        pytz.UTC.localize(at),
        [
            make_incident(
                service=make_service(rotation="emea"),
                opened_at=pytz.UTC.localize(opened_at),
            )
        ],
    )

    assert note == (
        f"Handoff emea - {expected_header}\n"
        f"- INC-4821 P2 Login fails for some customers (open since {expected_opened})"
    )
