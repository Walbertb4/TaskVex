"""TaskVex native start: run in v1 with python -m app.main.

The current UI is served via native HTTP from the same directory; ES modules have the file:// constraint
It doesn't get stuck. PyWebView's Edge/WebView2 engine is mandatory; We don't fall back on the old IE engine.
Native profile and settings are kept separate from the source code under TASKVEX_HOME.
"""

from contextlib import closing
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
    """On existing Bottle server, present UI with new file paths on every startup.

    The same origin and WebView profile is preserved: user storage is not deleted.
    Only the asset path is renewed; legacy HTML/new JS or legacy import will not interfere.
    The no-store header should be added to the actual response returned by Bottle.
    """
    from bottle import Bottle, HTTPResponse, static_file

    app = Bottle()
    prefix = uuid4().hex
    headers = {"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache", "Expires": "0"}

    def index():
        return HTTPResponse(status=302, headers={**headers, "Location": f"/{prefix}/index.html"})

    def asset(filename):
        # The path boundary, MIME and file source closure remain in the current Bottle.
        return static_file(filename, root=str(ui.parent), headers=headers)

    app.route("/", method="GET", callback=index)
    app.route(f"/{prefix}/<filename:path>", method="GET", callback=asset)
    return app


def main() -> None:
    """Open window in main thread; Shut down core on shutdown or startup error."""
    parser = argparse.ArgumentParser(description="TaskVex native desktop")
    parser.add_argument("--debug", action="store_true", help="Enable native developer tools")
    args = parser.parse_args()
    # Dependency errors are also detected by run()
    # be transformed; Running --help should not require a native library.
    from app.tools.local.clocks import Clocks
    from app.tools.local.telemetry import Telemetry
    from app.tools.local.media import Media
    from app.bootstrap import create_core
    from app.bridge.webview_bridge import NativeBridge
    from app.storage.json_store import JsonStore
    # The native desktop UI's startup sound should not wait for a click. Only this process
    # We set the WebView2 argument; Windows/general Edge policy remains unchanged.
    browser_args = os.environ.get("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "")
    if "--autoplay-policy=no-user-gesture-required" not in browser_args.split():
        os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = (
            browser_args + " --autoplay-policy=no-user-gesture-required"
        ).strip()
    import webview
    # Backup export uses the native Save File dialog; default download
    # When blocking was on, the Blob download request would be silently canceled.
    webview.settings["ALLOW_DOWNLOADS"] = True

    home = get_data_home()
    # Single owner of the entire native/core lifecycle for the same data root.
    # Restart opens the new process only after this lock is released.
    with SingleInstance(home):
        ui = Path(__file__).resolve().parents[1] / "ui" / "index.html"
        if not ui.is_file():
            raise FileNotFoundError("TaskVex UI index.html is missing")
        clocks = Clocks()
        media = Media()
        settings_store = JsonStore(home / "settings.json")
        with closing(Telemetry()) as telemetry, create_core(clocks=clocks, settings_store=settings_store, telemetry=telemetry, media=media) as core:
            bridge = NativeBridge(core, settings_store, clocks=clocks, telemetry=telemetry, media=media)
            window = webview.create_window("TaskVex", _ui_app(ui), js_api=bridge,
                                           http_port=webview.settings["DEFAULT_HTTP_PORT"],
                                           width=1280, height=800, min_size=(900, 600),
                                           background_color="#080b10")
            if window is None:
                raise RuntimeError("Native window could not be created")
            bridge._window = window
            # The X button should not shut down the core while the network turn is in progress. Live turn with Stop
            # can be closed after finishing; In REST, the turn finish is still awaited.
            window.events.closing += bridge._chat.close
            try:
                # WSGI app opens its own SDK server; Opening a second global server.
                webview.start(gui="edgechromium", debug=args.debug, http_server=False,
                              private_mode=False, storage_path=str(home / "webview"))
            finally:
                bridge._chat._live.close()  # Also drop resource I/O if the GUI loop ends unexpectedly.
    if bridge._restart_requested:
        # Reboot with the same trusty Python/entrypoint and data medium. Shell
        # not used; The second worker or window will not be started before the core is closed.
        command = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, "-m", "app.main"]
        if args.debug:
            command.append("--debug")
        subprocess.Popen(command, cwd=str(ui.parent.parent))


def _show_startup_error(error: Exception) -> None:
    """Prompt with terminal + Windows error box when the window cannot be opened at all.

    The raw exception message may contain file path or custom content; default
    messages are fixed. If the box itself cannot be opened, the terminal notification is retained.
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
    """Make unexpected startup error visible in CLI login and exit with error code."""
    try:
        main()
    except Exception as error:
        _show_startup_error(error)
        raise SystemExit(1) from None


if __name__ == "__main__":
    run()
