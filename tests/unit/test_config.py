import pytest
import pytz

from incidentdesk.config import settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    settings.cache_clear()
    yield
    settings.cache_clear()


def test_settings_defaults_to_chicago_timezone(monkeypatch):
    monkeypatch.delenv("INCIDENTDESK_TIMEZONE", raising=False)

    assert settings().timezone == "America/Chicago"


def test_settings_uses_configured_timezone(monkeypatch):
    monkeypatch.setenv("INCIDENTDESK_TIMEZONE", "Europe/Lisbon")

    assert settings().timezone == "Europe/Lisbon"


def test_settings_fails_for_unknown_timezone(monkeypatch):
    monkeypatch.setenv("INCIDENTDESK_TIMEZONE", "Not/A_Timezone")

    with pytest.raises(pytz.UnknownTimeZoneError):
        settings()
