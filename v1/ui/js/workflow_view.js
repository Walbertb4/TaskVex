/** Current host tasks only; TaskManager owns progress, cancellation and actual effects. */
import {emit, isBackendAvailable, createPendingOperation} from './api.js';
import {sfx} from './sfx.js';

let started = false, querying = false, epoch = 0, tasks = [], selected = null, pending = null, fresh = false;
let notice = '';
const el = id => document.getElementById(id);
const operation = createPendingOperation(() => {
  notice = 'Stop result unknown. Controls stay locked; no automatic retry.'; render();
});
export function startWorkflowView() { started = true; }
function render() {
  const panel = el('workflowPanel');
  if (!panel) return;
  panel.hidden = !tasks.length && !pending;
  const menu = el('workflowSelect');
  const choices = [['', 'Select a task…'], ...tasks.map(task => [task.workflow_id, `${task.workflow_id} · ${task.status}`])];
  if (menu.dataset.choices !== JSON.stringify(choices)) {
    menu.replaceChildren(...choices.map(([id, text]) => {
      const option = document.createElement('option'); option.value = id; option.textContent = text; return option;
    }));
    menu.dataset.choices = JSON.stringify(choices);
  }
  menu.value = selected || '';
  menu.disabled = !!pending || !fresh || !isBackendAvailable();
  const task = tasks.find(task => task.workflow_id === selected);
  el('workflowStop').disabled = !!pending || !fresh || !isBackendAvailable() || !task || task.completed || task.stop_requested;
  el('workflowDetails').textContent = task ? JSON.stringify({
    task: task.workflow_id, revision: task.revision, status: task.status,
    completed: task.completed, stop_requested: task.stop_requested,
    requires_review: task.requires_review, wait_reason: task.wait_reason, steps: task.steps
  }, null, 2) : '';
  el('workflowStatus').textContent = notice || (task?.stop_requested && !task.completed ?
    'Stop accepted. Waiting for actual completion; completed effects are preserved.' :
    task?.completed ? `Task ${task.status}. Completed effects are preserved.` : 'Progress only. Continue requires a trusted host recheck.');
}
function settle() { operation.finish(); pending = null; epoch++; notice = ''; }
export async function refreshWorkflows() {
  if (!started || querying || !isBackendAvailable()) return;
  querying = true;
  const version = epoch;
  try {
    const response = await emit('query_workflows');
    if (version !== epoch) return;
    const data = response.response?.data;
    if (!response.ok || !Array.isArray(data) || data.some(task => !task ||
      typeof task.workflow_id !== 'string' || !Number.isInteger(task.revision) || task.revision < 0 ||
      typeof task.status !== 'string' || typeof task.completed !== 'boolean' || typeof task.stop_requested !== 'boolean')) {
      fresh = false; if (!pending) notice = 'Task progress unavailable. Refreshing; no action sent.'; render(); return;
    }
    tasks = data; fresh = true;
    if (pending) {
      const actual = tasks.find(task => task.workflow_id === pending.workflow_id);
      // Absence or a different task cannot settle an unconfirmed Stop.
      if (actual && (actual.stop_requested || actual.completed)) settle();
    } else notice = '';
    if (!pending && !tasks.some(task => task.workflow_id === selected)) selected = null;
    render();
  } finally { querying = false; }
}
async function stopSelected() {
  const task = tasks.find(task => task.workflow_id === selected);
  if (!fresh || pending || !task || task.completed || task.stop_requested || !isBackendAvailable()) return;
  const intent = {workflow_id: task.workflow_id, revision: task.revision};
  pending = intent; epoch++; notice = 'Requesting Stop; waiting for the task owner.'; sfx.blip();
  const attempt = operation.begin(); render();
  const response = await emit('cancel_workflow', intent);
  if (!operation.isCurrent(attempt) || pending !== intent) return;
  if (response.ok && response.response?.accepted === true && response.response?.data?.workflow_id === intent.workflow_id) {
    const result = response.response.data;
    settle(); tasks = tasks.map(task => task.workflow_id === result.workflow_id ? result : task); render();
  } else if (!response.ok && response.response?.accepted === false) {
    settle(); fresh = false; notice = 'Stop was not accepted. Refreshing the current task; no automatic retry.'; render();
  } else operation.markUnknown();
  void refreshWorkflows();
}
export function initWorkflowView() {
  el('workflowSelect')?.addEventListener('change', event => {
    if (pending) return;
    selected = event.target.value; notice = ''; render();
  });
  el('workflowStop')?.addEventListener('click', () => { void stopSelected(); });
  render();
}
