/** Native host consent only; a decision never claims task/effect completion. */
import {emit, isBackendAvailable, createPendingOperation} from './api.js';
import {sfx} from './sfx.js';

let current = null, activeDecision = null, receipt = null, querying = false, revision = 0, unknown = false, started = false;
export function startTaskPermissions() { started = true; }
const status = text => { const el = document.getElementById('taskPermissionStatus'); if (el) el.textContent = text; };
const operation = createPendingOperation(() => {
  unknown = true; status('Decision result unknown. Controls stay locked; no automatic retry.'); controls();
});
function controls() {
  for (const id of ['taskPermissionApprove', 'taskPermissionReject']) {
    const button = document.getElementById(id);
    if (button) button.disabled = !current || !!activeDecision || unknown || !isBackendAvailable();
  }
}
function render(prompt) {
  const panel = document.getElementById('taskPermission');
  if (!panel) return;
  current = prompt;
  panel.hidden = !prompt && !activeDecision && !unknown;
  if (prompt) {
    document.getElementById('taskPermissionTitle').textContent = {
      scope: 'Expand task resource access?', input: 'Allow keyboard/mouse control for this task?',
      operation: 'Approve this high-impact operation?'
    }[prompt.kind] || 'Task permission';
    // External labels/arguments remain data; never render them as HTML/instructions.
    document.getElementById('taskPermissionDetails').textContent = JSON.stringify({
      task: prompt.task_id, step: prompt.step_id, tool: prompt.tool,
      arguments: prompt.arguments, resources: prompt.resources
    }, null, 2);
  }
  controls();
}
function finish(decision) {
  operation.finish(); activeDecision = null; unknown = false; revision++;
  receipt = decision.id;
  render(null);
  document.getElementById('taskPermission').hidden = false;
  status(decision.outcome === 'approved' ? 'Permission accepted. The task requires a host recheck before continuing.' :
    decision.outcome === 'denied' ? 'Permission denied. The task remains paused.' : 'This permission request is no longer current.');
}
export async function refreshTaskPermissions() {
  if (!started || querying || !isBackendAvailable()) return;
  querying = true;
  const version = revision;
  try {
    const result = await emit('query_task_permissions');
    if (!result.ok || version !== revision || !result.response?.data) return;
    const data = result.response.data;
    if (!Array.isArray(data.pending) || !Array.isArray(data.decisions)) return;
    if (activeDecision) {
      const decided = data.decisions.find(item => item.id === activeDecision);
      if (!decided) return; // Disappearance alone is not approval or evidence of failure.
      finish(decided);
    }
    const prompt = data.pending[0] || null;
    if (prompt?.id !== current?.id) { revision++; receipt = null; status(''); render(prompt); }
    else if (!prompt && receipt && data.decisions.some(item => item.id === receipt && item.task_completed)) {
      receipt = null; render(null);
    }
  } finally { querying = false; }
}
async function decide(approve) {
  if (!current || activeDecision || unknown) return;
  const id = current.id;
  activeDecision = id; revision++; sfx.blip(); controls();
  const attempt = operation.begin();
  const result = await emit('task_permission_decision', {id, approve});
  if (!operation.isCurrent(attempt) || activeDecision !== id) return;
  if (result.ok && result.response?.id === id && result.response.accepted === true) finish(result.response);
  else operation.markUnknown();
  void refreshTaskPermissions();
}
export function initTaskPermissions() {
  document.getElementById('taskPermissionApprove')?.addEventListener('click', () => { void decide(true); });
  document.getElementById('taskPermissionReject')?.addEventListener('click', () => { void decide(false); });
  controls();
}
