# Instructions for Copilot in incidentdesk

- Every change that users can notice (a new command, flag, endpoint or field, or a changed rule) adds one line to
  CHANGELOG.md under "## Unreleased", in plain words for the on-call engineers who use IncidentDesk.

- A pull request for a sub-issue of an epic ends its description with a handoff note: a link to the plan (`docs/plans/<issue number>.md`) and each test that proves a success criterion, by name (`test_...`). Keep the note when you rewrite the description.
