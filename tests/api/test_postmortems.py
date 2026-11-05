import pytest

from incidentdesk.seed import seed

pytestmark = pytest.mark.db


def test_demo_data_loads(db):
    counts = seed(reset=True)
    assert counts["services"] == 12 and counts["incidents"] > 200


def test_published_postmortems_only_by_default(client):
    seed(reset=True)
    published = client.get("/postmortems").json()
    everything = client.get("/postmortems", params={"include_drafts": True}).json()
    assert len(everything) > len(published)
    assert all(pm["published_at"] for pm in published)


def test_postmortem_by_key(client):
    seed(reset=True)
    key = client.get("/postmortems").json()[0]["key"]
    pm = client.get(f"/postmortems/{key}").json()
    assert pm["key"] == key and pm["incident"].startswith("INC-")
    assert client.get("/postmortems/PM-1").status_code == 404


def test_export_postmortem_as_markdown(client):
    seed(reset=True)
    response = client.get("/postmortems/PM-101/export.md")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    markdown = response.text
    assert markdown.startswith(
        "# PM-101: Billing service is down\n\n"
        "> Incident INC-4708 · Severity critical · Published 2026-08-17\n"
    )
    assert markdown.index("## Summary") < markdown.index("## Impact")
    assert markdown.index("## Impact") < markdown.index("## Root cause")
    assert markdown.index("## Root cause") < markdown.index("## Actions")
    assert "Billing Service is down for 81 minutes." in markdown
    assert (
        "- [ ] Automate certificate rotation checks (owner: payments)\n"
        "- [ ] Move reports to the read replica (owner: payments)"
    ) in markdown


def test_export_postmortem_requires_root_cause(client):
    seed(reset=True)
    assert client.get("/postmortems/PM-1/export.md").status_code == 404
    assert client.get("/postmortems/PM-117/export.md").status_code == 409
