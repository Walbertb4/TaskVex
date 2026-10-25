"""Keep core tests away from the user's application data."""

import pytest


@pytest.fixture(autouse=True)
def taskvex_home(tmp_path, monkeypatch):
    home = tmp_path / "taskvex"
    monkeypatch.setenv("TASKVEX_HOME", str(home))
    return home


@pytest.fixture(autouse=True)
def isolate_gpu_counters(monkeypatch):
    """Reading actual hardware in public suite; adapter tests provide fake PDH."""
    def unavailable(): raise OSError('Synthetic unavailable counters')
    monkeypatch.setattr('app.tools.local.windows_gpu._load_pdh',unavailable)


@pytest.fixture(autouse=True)
def isolate_network_counters(monkeypatch):
    """Standard tests do not access actual interface information or the internet."""
    def unavailable(): raise OSError('Synthetic unavailable interfaces')
    monkeypatch.setattr('app.tools.local.network._load_iphelper',unavailable)


@pytest.fixture(autouse=True)
def isolate_network_quality(monkeypatch):
    """Actual ping or Wi-Fi query initiation in tests; adapter tests emulate the DLL."""
    def unavailable(): raise OSError('Synthetic unavailable network quality')
    monkeypatch.setattr('app.tools.local.network_quality._load_iphelper',unavailable)
    monkeypatch.setattr('app.tools.local.network_quality._load_wlan',unavailable)


@pytest.fixture(autouse=True)
def isolate_media(monkeypatch):
    """The tests do not query the user's actual track/media history."""
    monkeypatch.setattr('app.tools.local.media._read_windows',lambda manager=None:{'status':'no_session'})
    def unavailable():raise OSError('Synthetic unavailable application audio')
    monkeypatch.setattr('app.tools.local.media_volume._load_audio',unavailable)


@pytest.fixture(autouse=True)
def isolate_weather(monkeypatch):
    """Weather tests inject public-provider transport; the suite never shares real locations."""
    from app.tools.services.weather import WeatherError
    def unavailable(*args):raise WeatherError('Synthetic unavailable weather')
    monkeypatch.setattr('app.tools.services.weather._request_json',unavailable)
