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
