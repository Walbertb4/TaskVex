"""Gerçek Windows apps.open kabulü: python tests/apps_open_smoke.py --report ...

pytest'e dahil değildir; bilinçli çalıştırılınca Not Defteri açabilir. Belgeleri
düzenlemez, kullanıcı sekmelerini kapatmaz. Test yalnız gerçek core hattındaki
başlatma sayısını gözler; Windows başlatıcısını veya gözlem sonucunu taklit etmez.
Varsayılan kayıt dizini yerine geçici TASKVEX_HOME kullanır.
"""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.bootstrap import create_core
from app.core.contracts import TaskStatus, ToolRequest
from app.tools.local import windows_apps


def main():
    """Aç/kabul/replay/yeniden istek hattını doğrula; kapatma yetkisi kullanma."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report, launches = {}, []
    original_start = windows_apps.start_notepad
    original_home = os.environ.get("TASKVEX_HOME")

    def counted_start(path):
        launches.append(True)
        return original_start(path)

    def query(core, tool, request_id):
        return core.wait(core.submit(ToolRequest(
            request_id=request_id, source="desktop", principal="local-user",
            tool=tool, arguments={"app_id": "notepad"},
        )).task_id, 15)

    try:
        windows_apps.start_notepad = counted_start
        with tempfile.TemporaryDirectory(prefix="taskvex-open-") as directory:
            os.environ["TASKVEX_HOME"] = directory
            with create_core() as core:
                before = query(core, "apps.status", "before")
                assert before.status == TaskStatus.SUCCEEDED, before.to_dict()
                opened = query(core, "apps.open", "open-once")
                assert opened.status == TaskStatus.SUCCEEDED, opened.to_dict()
                assert opened.result.data["running"] and opened.result.data["visible_window"]
                replay = query(core, "apps.open", "open-once")
                assert replay.task_id == opened.task_id
                again = query(core, "apps.open", "open-new-request")
                assert again.status == TaskStatus.SUCCEEDED, again.to_dict()
                assert again.result.data["already_open"] and not again.result.data["launch_requested"]
                expected = 0 if before.result.data["visible_window"] or before.result.data["running"] else 1
                assert len(launches) == expected
                report = {"ok": True, "launch_count": len(launches),
                          "fresh_launch_checked": expected == 1, "replay_same_task": True,
                          "second_request_reused_window": True,
                          "before": before.result.to_dict(), "opened": opened.result.to_dict(),
                          "again": again.result.to_dict(), "application_left_open": True}
    finally:
        windows_apps.start_notepad = original_start
        if original_home is None:
            os.environ.pop("TASKVEX_HOME", None)
        else:
            os.environ["TASKVEX_HOME"] = original_home
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True))


if __name__ == "__main__":
    main()
