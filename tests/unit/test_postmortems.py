from incidentdesk.models import Postmortem
from incidentdesk.postmortems import missing_sections


def test_no_sections_are_missing_when_all_are_filled():
    postmortem = Postmortem(
        summary="Summary",
        impact="Impact",
        root_cause="Root cause",
        actions=["Action"],
    )

    assert missing_sections(postmortem) == []


def test_root_cause_is_missing_from_draft():
    postmortem = Postmortem(
        summary="Summary",
        impact="Impact",
        root_cause=None,
        actions=["Action"],
    )

    assert missing_sections(postmortem) == ["root_cause"]


def test_empty_postmortem_has_all_sections_missing_in_order():
    postmortem = Postmortem(
        summary="",
        impact="",
        root_cause=None,
        actions=[],
    )

    assert missing_sections(postmortem) == ["summary", "impact", "root_cause", "actions"]
