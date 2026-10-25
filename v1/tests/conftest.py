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
    monkeypatch.setattr('app.tools.local.media._read_windows',lambda:{'status':'no_session'})
