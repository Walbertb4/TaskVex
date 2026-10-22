"""İsteğe bağlı gerçek Gemini kabulü; varsayılan yalnız uygulama kataloğunu okur.

v1 içinde: python tests/gemini_smoke.py --report ../docs/stage5-gemini-live.json
Anahtar GEMINI_API_KEY veya Windows kimlik deposundan gelir. --notes seçilirse yalnız
geçici dizindeki sentetik not kullanılır. Gerçek kullanıcı notları gönderilmez.
Betik import edilince ağ isteği, dosya yazma veya model oturumu başlatmaz.
"""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.bootstrap import create_core
from app.core.contracts import ContractError
from app.session.gemini import DEFAULT_MODEL, GeminiText
from app.session.model_tools import ModelTools
from app.storage.json_store import JsonStore
from app.storage.credentials import CredentialError, load_gemini_key


def main() -> int:
    """Tek canlı tur yap; modelin sözü yerine gerçek araç kayıtlarını denetle."""
    parser = argparse.ArgumentParser(description="TaskVex optional live Gemini acceptance")
    parser.add_argument("--notes", action="store_true", help="Use only a temporary synthetic note")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Generate Content text model; not a Live model")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    key_error = False
    try:
        key = load_gemini_key()  # Test profiline geçmeden gerçek host profilinin anahtarını al.
    except (CredentialError, ContractError):
        key = None
        key_error = True
    if key is None:
        report = {"ok": False, "code": "credential_unavailable" if key_error else "missing_api_key",
                  "live_request_made": False}
    else:
        original_home = os.environ.get("TASKVEX_HOME")
        try:
            with tempfile.TemporaryDirectory(prefix="taskvex-gemini-") as directory:
                os.environ["TASKVEX_HOME"] = directory
                names = ("notes.add", "notes.list") if args.notes else ("apps.catalog",)
                text = ("Use notes.add to add exactly one note whose text is 'TaskVex API acceptance'. "
                        "Then use notes.list to read it back. Do not add any other notes."
                        if args.notes else "Use apps.catalog to list supported apps. Base your answer on its result.")
                with create_core() as core:
                    tools = ModelTools(core, principal="local-user", session_id=uuid4().hex, allowed_tools=names)
                    with GeminiText(tools, model=args.model, api_key=key) as model:
                        report = model.run(text)
                verified = {item["name"] for item in report["tool_results"]
                            if item["status"] == "succeeded" and item["result"]["verified"]}
                checked = set(names) <= verified
                if args.notes:
                    document = JsonStore(Path(directory) / "notes.json").read()
                    notes = document["notes"] if document else []
                    checked = checked and len(notes) == 1 and notes[0]["text"] == "TaskVex API acceptance"
                    # Yalnız araç adlarının görünmesi yetmez: not eklenmeden
                    # önceki boş liste, eklenen notun geri okunması sayılamaz.
                    checked = checked and any(
                        item["name"] == "notes.list" and item["status"] == "succeeded"
                        and item["result"]["verified"] and item["result"]["data"]["notes"] == notes
                        for item in report["tool_results"]
                    )
                report.update(requested_model=args.model, scenario="temporary_notes" if args.notes else "catalog",
                              live_request_made=True, acceptance_verified=checked)
                report["ok"] = report["ok"] and checked
        except ContractError:
            report = {"ok": False, "code": "configuration_or_core_error"}
        finally:
            if original_home is None:
                os.environ.pop("TASKVEX_HOME", None)
            else:
                os.environ["TASKVEX_HOME"] = original_home
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
