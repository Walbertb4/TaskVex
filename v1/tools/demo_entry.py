"""Packaged demo entry point; It uses the normal app.main owner.

The demo profile is separate from developer data. --setup-wake by explicit user request
upstream lowers the weights; model weights are not distributed in this package.
--smoke-report is just an internal packet acceptance test with temporary TASKVEX_HOME.
"""
import json
import os
from pathlib import Path
import sys
import time
import traceback


def smoke(report: Path):
    """Real packet/WebView2 opening; There is no API, no microphone, and no private media data."""
    if not os.environ.get('TASKVEX_HOME'):
        raise ValueError('Smoke requires an explicit temporary profile')
    import webview
    import sherpa_onnx
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
    from app.tools.local import media
    media._read_windows = lambda: {'status':'no_session'}
    from app.main import main
    original_create, original_start = webview.create_window, webview.start
    captured = {}
    outcome = {'ok':False,'frozen':bool(getattr(sys,'frozen',False)),
        'wake_runtime':sherpa_onnx.__version__, 'winrt_import':GlobalSystemMediaTransportControlsSessionManager is not None}

    def create(*args, **kwargs):
        kwargs['hidden'] = True
        captured['bridge'] = kwargs['js_api']
        window = original_create(*args, **kwargs)
        captured['window'] = window
        return window

    def exercise():
        window = captured['window']
        try:
            deadline = time.monotonic()+25
            while time.monotonic()<deadline:
                if captured['bridge']._ready and window.evaluate_js("!!window.vex && document.getElementById('ram').textContent.includes('%')"):
                    break
                time.sleep(.2)
            else:
                raise RuntimeError('Packaged UI not ready')
            result = window.evaluate_js("({ready:!!window.vex,media:document.getElementById('mTitle2').textContent,"
                "api:document.getElementById('netP').textContent,styles:document.styleSheets.length})")
            assert 'OFFLINE' in result['api'] and result['styles']>0
            outcome.update(ok=True,ui_ready=True,styles_loaded=True,no_provider_connected=True)
        except Exception as error:
            outcome.update(error=type(error).__name__)
        finally:
            report.write_text(json.dumps(outcome,indent=2),encoding='utf-8')
            window.destroy()

    def start(**kwargs):
        original_start(func=exercise,**kwargs)
    webview.create_window, webview.start = create, start
    sys.argv = [sys.argv[0]]
    main()
    if not outcome['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    for stream in ('stdout','stderr'):
        if getattr(sys,stream) is None:
            setattr(sys,stream,open(os.devnull,'w'))
    if len(sys.argv)==3 and sys.argv[1]=='--smoke-report':
        report = Path(sys.argv[2])
        try:
            smoke(report)
        except Exception as error:
            report.write_text(json.dumps({'ok':False,'error':type(error).__name__,'trace':traceback.format_exc()},indent=2),encoding='utf-8')
            raise SystemExit(1)
    else:
        os.environ.setdefault('TASKVEX_HOME',str(Path(os.environ['LOCALAPPDATA'])/'TaskVexDemo'))
        if sys.argv[1:]==['--setup-wake']:
            import ctypes
            try:
                from app.session.wake_word import setup
                setup()
                ctypes.windll.user32.MessageBoxW(None,'Wake model setup finished. You can open TaskVexDemo.','TaskVex Demo',0x40)
            except Exception:
                ctypes.windll.user32.MessageBoxW(None,'Wake model setup failed. Check your internet connection and retry.','TaskVex Demo',0x10)
                raise SystemExit(1)
        else:
            from app.main import run
            run()
