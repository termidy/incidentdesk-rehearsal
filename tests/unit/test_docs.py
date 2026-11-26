import re
import shlex
from pathlib import Path

import pytest

from incidentdesk.cli import build_parser


ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs" / "runbook.md"


def check_runbook(text):
    for reference in re.findall(r"`([^`\n]+)`", text):
        if re.fullmatch(r"(?:[\w.-]+/)*[\w.-]+\.(?:py|sh|md|ya?ml|json)", reference):
            assert (ROOT / reference).is_file(), f"Missing file: {reference}"

    blocks = re.findall(r"```bash\n(.*?)\n```", text, re.DOTALL)
    assert blocks, "No runbook commands found"
    for block in blocks:
        for line in block.splitlines():
            words = shlex.split(line)
            if not words:
                continue
            for word in words:
                if word.startswith("scripts/"):
                    assert (ROOT / word).is_file(), f"Missing script: {word}"
            if words[0] == "incidentdesk":
                try:
                    build_parser().parse_args(words[1:])
                except SystemExit as error:
                    raise AssertionError(f"Invalid incidentdesk command: {line}") from error


def test_runbook_references_exist():
    check_runbook(RUNBOOK.read_text())


def test_runbook_check_rejects_renamed_subcommand():
    text = RUNBOOK.read_text().replace("incidentdesk sla\n", "incidentdesk missing-command\n")
    assert text != RUNBOOK.read_text()
    with pytest.raises(AssertionError, match="Invalid incidentdesk command"):
        check_runbook(text)


def test_runbook_check_rejects_renamed_script():
    text = RUNBOOK.read_text().replace("scripts/test.sh\n", "scripts/missing.sh\n")
    assert text != RUNBOOK.read_text()
    with pytest.raises(AssertionError, match="Missing script"):
        check_runbook(text)
