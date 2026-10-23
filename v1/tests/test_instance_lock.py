"""Tek-instance kilidini geçici klasör ve gerçek alt süreçle doğrular.

Gerçek kullanıcı verisi, native pencere veya API kullanılmaz. Çöken sürecin
dosyayı geride bırakmasının uygulamayı kalıcı engellemediği ayrıca sınanır.
"""
import subprocess
import sys

import pytest

from app.storage.instance_lock import AlreadyRunningError, SingleInstance


def test_second_process_rejected_and_normal_exit_releases(tmp_path):
    code = """
import sys
from pathlib import Path
from app.storage.instance_lock import SingleInstance, AlreadyRunningError
try:
    with SingleInstance(Path(sys.argv[1])):
        print('acquired')
except AlreadyRunningError:
    print('blocked')
"""
    def attempt():
        return subprocess.check_output([sys.executable, '-c', code, str(tmp_path)], text=True).strip()
    with SingleInstance(tmp_path):
        assert attempt() == 'blocked'
        with pytest.raises(AlreadyRunningError):
            with SingleInstance(tmp_path / 'alias' / '..'):
                pytest.fail('alias bypassed lock')
        with SingleInstance(tmp_path / 'separate-profile'):
            pass
    assert attempt() == 'acquired'
    assert (tmp_path / 'instance.lock').is_file()


def test_crash_releases_os_lock_without_deleting_file(tmp_path):
    code = """
import sys
from pathlib import Path
from app.storage.instance_lock import SingleInstance
with SingleInstance(Path(sys.argv[1])):
    print('ready', flush=True)
    sys.stdin.read()
"""
    child = subprocess.Popen([sys.executable, '-c', code, str(tmp_path)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == 'ready'
        with pytest.raises(AlreadyRunningError):
            with SingleInstance(tmp_path):
                pytest.fail('child lock was ignored')
    finally:
        child.kill()
        child.communicate(timeout=10)
    with SingleInstance(tmp_path):
        pass


def test_exception_releases_lock(tmp_path):
    with pytest.raises(ValueError):
        with SingleInstance(tmp_path):
            raise ValueError('synthetic failure')
    with SingleInstance(tmp_path):
        pass


def test_native_start_refuses_before_starting_core(tmp_path, monkeypatch):
    from app import main as entry
    from app import bootstrap
    monkeypatch.setenv('TASKVEX_HOME', str(tmp_path))
    monkeypatch.setattr(sys, 'argv', ['taskvex'])
    monkeypatch.setattr(bootstrap, 'create_core', lambda **kwargs: pytest.fail('second worker started'))
    with SingleInstance(tmp_path):
        with pytest.raises(AlreadyRunningError):
            entry.main()
