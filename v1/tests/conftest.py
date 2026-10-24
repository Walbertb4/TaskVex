"""Keep core tests away from the user's application data."""

import pytest


@pytest.fixture(autouse=True)
def taskvex_home(tmp_path, monkeypatch):
    home = tmp_path / "taskvex"
    monkeypatch.setenv("TASKVEX_HOME", str(home))
    return home


@pytest.fixture(autouse=True)
def isolate_gpu_counters(monkeypatch):
    """Genel süitte gerçek donanımı okuma; adaptör testleri sahte PDH sağlar."""
    def unavailable(): raise OSError('Synthetic unavailable counters')
    monkeypatch.setattr('app.tools.local.windows_gpu._load_pdh',unavailable)


@pytest.fixture(autouse=True)
def isolate_network_counters(monkeypatch):
    """Standart testler gerçek arabirim bilgisine veya internete erişmez."""
    def unavailable(): raise OSError('Synthetic unavailable interfaces')
    monkeypatch.setattr('app.tools.local.network._load_iphelper',unavailable)


@pytest.fixture(autouse=True)
def isolate_network_quality(monkeypatch):
    """Testlerde gerçek ping veya Wi-Fi sorgusu başlatma; adaptör testleri DLL'i taklit eder."""
    def unavailable(): raise OSError('Synthetic unavailable network quality')
    monkeypatch.setattr('app.tools.local.network_quality._load_iphelper',unavailable)
    monkeypatch.setattr('app.tools.local.network_quality._load_wlan',unavailable)
