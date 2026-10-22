"""Keep core tests away from the user's application data."""

import pytest


@pytest.fixture(autouse=True)
def taskvex_home(tmp_path, monkeypatch):
    home = tmp_path / "taskvex"
    monkeypatch.setenv("TASKVEX_HOME", str(home))
    return home
