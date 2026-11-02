import pytest

from incidentdesk import __version__
from incidentdesk.cli import main


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == f"incidentdesk {__version__}\n"
