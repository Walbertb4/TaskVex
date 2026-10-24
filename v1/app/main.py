"""TaskVex native başlangıcı: v1 içinde python -m app.main ile çalıştır.

Mevcut UI aynı dizinden yerel HTTP ile sunulur; ES modülleri file:// kısıtına
takılmaz. PyWebView'in Edge/WebView2 motoru zorunludur; eski IE motoruna düşmeyiz.
Native profil ve ayarlar TASKVEX_HOME altında kaynak koddan ayrı tutulur.
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from app.config import get_data_home
from app.core.contracts import ContractError
from app.storage.instance_lock import AlreadyRunningError, SingleInstance


def _ui_app(ui: Path):
    """Mevcut Bottle sunucusunda UI'ı her açılışta yeni dosya yollarıyla sun.

    Aynı origin ve WebView profili korunur: kullanıcı depolaması silinmez.
    Yalnız asset yolu yenilenir; eski HTML/yeni JS veya eski import karışmaz.
    no-store başlığı Bottle'ın döndürdüğü gerçek yanıta eklenmelidir.
    """
    from bottle import Bottle, HTTPResponse, static_file

    app = Bottle()
    prefix = uuid4().hex
    headers = {"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache", "Expires": "0"}

    def index():
        return HTTPResponse(status=302, headers={**headers, "Location": f"/{prefix}/index.html"})

    def asset(filename):
        # Yol sınırı, MIME ve dosya kaynak kapanışı mevcut Bottle'da kalır.
        return static_file(filename, root=str(ui.parent), headers=headers)

    app.route("/", method="GET", callback=index)
    app.route(f"/{prefix}/<filename:path>", method="GET", callback=asset)
    return app


def main() -> None:
    """Pencereyi ana thread'de aç; kapanış veya başlangıç hatasında core'u kapat."""
    parser = argparse.ArgumentParser(description="TaskVex native desktop")
    parser.add_argument("--debug", action="store_true", help="Enable native developer tools")
    args = parser.parse_args()
    # Bağımlılık hataları da run() tarafından anlaşılır başlangıç hatasına
    # dönüştürülebilsin; --help çalıştırmak native kütüphane gerektirmesin.
    from app.tools.local.clocks import Clocks
    from app.bootstrap import create_core
    from app.bridge.webview_bridge import NativeBridge
    from app.storage.json_store import JsonStore
    # Yerel masaüstü UI'ın açılış sesi tıklama beklememeli. Yalnız bu sürecin
    # WebView2 argümanını ayarlarız; Windows/genel Edge politikası değişmez.
    browser_args = os.environ.get("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "")
    if "--autoplay-policy=no-user-gesture-required" not in browser_args.split():
        os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = (
            browser_args + " --autoplay-policy=no-user-gesture-required"
        ).strip()
    import webview
    # Yedek export'u native Save File diyaloğunu kullanır; varsayılan indirme
    # engeli açıkken Blob download isteği sessizce iptal edilirdi.
    webview.settings["ALLOW_DOWNLOADS"] = True

    home = get_data_home()
    # Aynı veri kökü için bütün native/core yaşam döngüsünün tek sahibi.
    # Restart yeni süreci ancak bu kilit bırakıldıktan sonra açar.
    with SingleInstance(home):
        ui = Path(__file__).resolve().parents[1] / "ui" / "index.html"
        if not ui.is_file():
            raise FileNotFoundError("TaskVex UI index.html is missing")
        clocks = Clocks()
        settings_store = JsonStore(home / "settings.json")
        with create_core(clocks=clocks, settings_store=settings_store) as core:
            bridge = NativeBridge(core, settings_store, clocks=clocks)
            window = webview.create_window("TaskVex", _ui_app(ui), js_api=bridge,
                                           http_port=webview.settings["DEFAULT_HTTP_PORT"],
                                           width=1280, height=800, min_size=(900, 600),
                                           background_color="#080b10")
            if window is None:
                raise RuntimeError("Native window could not be created")
            bridge._window = window
            # X düğmesi ağ turu sürerken core'u kapatmamalı. Live turu Stop ile
            # bitirildikten sonra kapanabilir; REST'te tur bitişi hâlâ beklenir.
            window.events.closing += bridge._chat.close
            try:
                # WSGI app kendi SDK sunucusunu açar; ikinci global sunucu açma.
                webview.start(gui="edgechromium", debug=args.debug, http_server=False,
                              private_mode=False, storage_path=str(home / "webview"))
            finally:
                bridge._chat._live.close()  # GUI döngüsü beklenmedik biçimde biterse de I/O kaynağını bırak.
    if bridge._restart_requested:
        # Aynı güvenilir Python/entrypoint ve veri ortamıyla yeniden aç. Shell
        # kullanılmaz; core kapanmadan ikinci worker veya pencere başlatılmaz.
        command = [sys.executable, "-m", "app.main"]
        if args.debug:
            command.append("--debug")
        subprocess.Popen(command, cwd=str(ui.parent.parent))


def _show_startup_error(error: Exception) -> None:
    """Pencere hiç açılamadığında terminal + Windows hata kutusuyla yol göster.

    Ham exception mesajı dosya yolu veya özel içerik taşıyabilir; varsayılan
    mesajlar sabittir. Kutunun kendisi açılamazsa terminal bildirimi korunur.
    """
    if isinstance(error, AlreadyRunningError):
        message = "TaskVex is already running for this data profile. Close the existing window before opening another instance."
    elif isinstance(error, ModuleNotFoundError):
        message = "Required app components are missing. Install requirements-dev.lock.txt using the project's .venv Python, then retry."
    elif isinstance(error, ContractError):
        message = "The data location is invalid. Set TASKVEX_HOME to an absolute directory, or remove it to use the default location."
    elif isinstance(error, FileNotFoundError):
        message = "A required application file is missing. Restore the TaskVex installation, then retry."
    elif isinstance(error, OSError):
        message = "TaskVex could not access required files or start the app. Check folder permissions, free disk space and the installation."
    else:
        message = "TaskVex could not open its native window. Check that Microsoft Edge WebView2 Runtime is installed, then retry."
    message += "\nYour saved data was not automatically reset."
    print("TaskVex startup failed: " + message, file=sys.stderr)
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, "TaskVex — startup failed", 0x10)
        except Exception:
            pass


def run() -> None:
    """CLI girişinde beklenmeyen açılış hatasını görünür kıl ve hata koduyla çık."""
    try:
        main()
    except Exception as error:
        _show_startup_error(error)
        raise SystemExit(1) from None


if __name__ == "__main__":
    run()
