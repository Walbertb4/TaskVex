"""Check development output routing without accounts, devices or native windows."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest


def load_script(name, monkeypatch):
    """Load the existing CLI without invoking its acceptance work."""
    folder = Path(__file__).parent
    monkeypatch.syspath_prepend(str(folder))
    spec = importlib.util.spec_from_file_location(f'output_test_{name}', folder / f'{name}.py')
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('explicit', [False, True])
def test_gemini_report_routing_without_provider(tmp_path, monkeypatch, explicit):
    """Missing-key reports still create nested directories and honor overrides."""
    script = load_script('gemini_smoke', monkeypatch)
    monkeypatch.setattr(script, '__file__', str(tmp_path / 'v1/tests/gemini_smoke.py'))
    monkeypatch.setattr(script, 'load_gemini_key', lambda: None)
    destination = tmp_path / ('custom/nested/result.json' if explicit else 'logs/reports/gemini-smoke.json')
    monkeypatch.setattr(sys, 'argv', ['gemini_smoke.py', *(['--report', str(destination)] if explicit else [])])
    assert script.main() == 1
    assert json.loads(destination.read_text(encoding='utf-8')) == {
        'ok': False, 'code': 'missing_api_key', 'live_request_made': False,
    }


def test_native_phase_logs_survive_profile_cleanup(tmp_path, monkeypatch):
    """Synthetic child output survives independently of disposable test profiles."""
    script = load_script('native_smoke', monkeypatch)
    monkeypatch.setattr(script, '__file__', str(tmp_path / 'v1/tests/native_smoke.py'))
    monkeypatch.setattr(sys, 'argv', ['native_smoke.py'])
    profiles = []

    class Child:
        def __init__(self, command, *, stdout, stderr):
            phase = command[command.index('--phase') + 1]
            home = Path(command[command.index('--home') + 1])
            home.mkdir(parents=True, exist_ok=True)
            profiles.append(home)
            (home / f'report-{phase}.json').write_text(json.dumps({'ok': True, 'phase': phase}))
            stdout.write(b'synthetic child diagnostics\n')

        def wait(self, timeout):
            return 0

    monkeypatch.setattr(script.subprocess, 'Popen', Child)
    script.run()
    assert all(not home.exists() for home in profiles)
    logs = list((tmp_path / 'logs/raw/native').glob('run-*/*.log'))
    assert len(logs) == 11
    assert all(path.read_bytes() == b'synthetic child diagnostics\n' for path in logs)
    report = json.loads((tmp_path / 'logs/reports/native-smoke.json').read_text(encoding='utf-8'))
    assert report['ok'] and len(report['phases']) == 11
