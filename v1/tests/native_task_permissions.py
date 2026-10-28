"""Native consent rendering/decisions with an actual synthetic scoped manager."""
from pathlib import Path
import tempfile

from test_task_permissions import build, prompt


def check_native_task_permissions(window, api, js, wait_until, outcome):
    js("const s=await import('./js/settings.js');s.loadStore({...s.store,askBeforeInput:false},{emitSave:false});return true;")
    assert window.evaluate_js("document.getElementById('askBeforeInput').checked===false")
    js("const s=await import('./js/settings.js');s.loadStore({...s.store,askBeforeInput:true},{emitSave:false});return true;")
    assert window.evaluate_js("document.getElementById('askBeforeInput').checked===true")
    original = api._core
    with tempfile.TemporaryDirectory(prefix='taskvex-permission-native-') as home:
        core, _, _, _, _, calls = build(Path(home))
        with core:
            api._core = core
            try:
                for kind in ('scope', 'input', 'operation'):
                    nonce = prompt(core)['id']
                    js("await (await import('./js/task_permissions.js')).refreshTaskPermissions();return true;")
                    wait_until(lambda: not window.evaluate_js("document.getElementById('taskPermission').hidden"))
                    assert window.evaluate_js("document.getElementById('taskPermissionDetails').textContent.includes('system.status')")
                    assert core.permission_view()['pending'][0]['kind'] == kind
                    js("document.getElementById('taskPermissionApprove').click();return true;")
                    wait_until(lambda: any(d['id'] == nonce and d['outcome'] == 'approved'
                                          for d in core.permission_view()['decisions']))
                    assert calls == []
                assert core.get_workflow('job')['status'] == 'waiting_for_user'
                outcome['native_task_consent_scope_input_operation_no_effect_before_host_recheck'] = True
            finally:
                api._core = original
    js("await (await import('./js/task_permissions.js')).refreshTaskPermissions();return true;")
    outcome['native_task_input_preference_form_and_text_consent'] = True
