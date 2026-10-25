"""UI cache fix: real Bottle/WSGI replies; The GUI or API does not open.

Origin/profile should not change file paths at every boot. Static import
The entire graph comes from the same new root; The old file response is not reused.
"""
from io import BytesIO
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from app.main import _ui_app


def request(app, path, **extra):
    """Observe the status/title/body given by the WSGI server without opening the network."""
    environ = {}
    setup_testing_defaults(environ)
    environ.update(PATH_INFO=path, **extra)
    environ['wsgi.input'] = BytesIO()
    response = {}
    def start(status, headers, exc_info=None):
        response.update(status=int(status.split()[0]), headers=dict(headers))
    result = app(environ, start)
    try:
        response['body'] = b''.join(result)
    finally:
        if hasattr(result, 'close'):
            result.close()
    return response


def test_all_ui_assets_have_no_store_and_launch_specific_paths(tmp_path):
    ui = tmp_path / 'ui'
    (ui / 'js').mkdir(parents=True)
    (ui / 'index.html').write_text('<script type="module" src="js/app.js"></script>', encoding='utf-8')
    script = ui / 'js/app.js'
    script.write_text('export const version = 1;', encoding='utf-8')
    app = _ui_app(ui / 'index.html')
    home = request(app, '/')
    assert home['status'] == 302 and 'no-store' in home['headers']['Cache-Control']
    index = home['headers']['Location']
    for path in [index, index.replace('index.html', 'js/app.js')]:
        response = request(app, path)
        assert response['status'] == 200 and 'no-store' in response['headers']['Cache-Control']
        assert response['headers']['Pragma'] == 'no-cache'
    script.write_text('export const version = 2;', encoding='utf-8')
    assert b'version = 2' in request(app, index.replace('index.html','js/app.js'))['body']
    next_app = _ui_app(ui / 'index.html')
    assert request(next_app, '/')['headers']['Location'] != index
    assert request(next_app, index)['status'] == 404
    assert request(app, index.replace('index.html','../secret.txt'))['status'] == 403


def test_real_module_import_graph_uses_current_settings_export():
    ui = Path(__file__).resolve().parents[1] / 'ui/index.html'
    app = _ui_app(ui)
    index = request(app, '/')['headers']['Location']
    base = index.removesuffix('index.html')
    assert b'getAudioDeviceId' in request(app, base + 'js/assistant_session.js')['body']
    assert b'getAudioDeviceId' in request(app, base + 'js/settings.js')['body']
    assert b'export function getAudioDeviceId' in request(app, base + 'js/devices.js')['body']
    assert request(app, base + 'js/live_audio.js')['status'] == 200
