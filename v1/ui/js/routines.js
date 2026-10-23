/**
 * routines.js - Yerel rutin tanımları/editörü; yürütme ve scheduler henüz yok.
 */

import { sfx } from './sfx.js';
import { logBridgeError } from './api.js';
import { normalizeRoutineSteps as normalizeSteps, uniqueRecordId, validateAndNormalizeSnapshot } from './schema.js';

let routines = [];
let rEdit = null;
let saveStoreCb = null;

const RT = {
  manual: 'Manual / voice',
  time: 'Time',
  app: 'App launch',
  wifi: 'Wi-Fi'
};

const RD = {
  all: 'every day',
  week: 'weekdays',
  wend: 'weekends'
};

const pad2 = n => String(n).padStart(2, '0');
const stamp = () => {
  const d = new Date();
  return `${pad2(d.getDate())}.${pad2(d.getMonth() + 1)} ${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
};



export function getRoutines() {
  return routines;
}

export function renderRoutines() {
  const container = document.getElementById('rtList');
  if (!container) return;

  container.innerHTML = '';
  if (!routines || routines.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'sub';
    empty.textContent = 'No routines yet.';
    container.append(empty);
    return;
  }

  routines.forEach(r => {
    const card = document.createElement('div');
    card.className = 'sk';

    const titleWrap = document.createElement('div');
    const b = document.createElement('b');
    b.textContent = r.name || 'Unnamed routine';

    const triggerDetails =
      ' · ' +
      (RT[r.type] || r.type) +
      (r.val ? ': ' + r.val : '') +
      (r.type === 'time' ? ' · ' + (RD[r.days || 'all'] || r.days) : '');

    const subTrig = document.createElement('span');
    subTrig.className = 'sub';
    subTrig.textContent = triggerDetails;
    titleWrap.append(b, subTrig);

    const safeSteps = normalizeSteps(r && r.steps);
    const stepsText = safeSteps ? safeSteps.split('\n').map(x => x.trim()).filter(Boolean).join(' → ') : '';
    const desc = document.createElement('div');
    desc.className = 'sub';
    desc.textContent = stepsText;

    card.append(titleWrap, desc);

    if (r.last) {
      const lastDiv = document.createElement('div');
      lastDiv.className = 'sub';
      lastDiv.style.margin = '0 0 8px';
      lastDiv.style.color = 'var(--gold)';
      lastDiv.textContent = 'last: ' + r.last + (r.ok === false ? ' ✗' : ' ✓');
      card.append(lastDiv);
    }

    const acts = document.createElement('div');
    acts.className = 'acts';
    acts.dataset.id = r.id;

    const lbl = document.createElement('label');
    lbl.className = 'sub';
    lbl.style.cssText = 'display:flex;gap:6px;align-items:center;margin:0 8px 0 0';

    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.dataset.a = 'on';
    cb.checked = !!r.on;
    lbl.append(cb, document.createTextNode('Active'));

    const runB = document.createElement('button');
    runB.className = 'cb';
    runB.dataset.a = 'run';
    runB.textContent = '▶ Run now';

    const editB = document.createElement('button');
    editB.className = 'cb';
    editB.dataset.a = 'edit';
    editB.textContent = 'Edit';

    const delB = document.createElement('button');
    delB.className = 'cb red';
    delB.dataset.a = 'del';
    delB.textContent = 'Delete';

    acts.append(lbl, runB, editB, delB);
    card.append(acts);
    container.append(card);
  });
}

export function runRoutine(r, src) {
  if (r) alert('Routine execution is not connected yet. Your definition is saved locally.');
}

function updateRoutineFormUI() {
  const rType = document.getElementById('rType');
  const rVal = document.getElementById('rVal');
  const rDaysW = document.getElementById('rDaysW');
  if (!rType || !rVal) return;

  const t = rType.value;
  rVal.disabled = t === 'manual';
  rVal.placeholder = t === 'time' ? '08:00' : t === 'app' ? 'Spotify.exe' : t === 'wifi' ? 'Wi-Fi name' : '—';
  if (rDaysW) rDaysW.style.display = t === 'time' ? '' : 'none';
}

function showRoutineError(msg) {
  let errEl = document.getElementById('rtErr');
  if (!errEl) {
    errEl = document.createElement('div');
    errEl.id = 'rtErr';
    errEl.style.cssText = 'color:#ff5d5d;font-size:12px;margin:8px 0;';
    const rtForm = document.getElementById('rtForm');
    if (rtForm) rtForm.prepend(errEl);
  }
  errEl.textContent = msg;
}

function clearRoutineError() {
  const errEl = document.getElementById('rtErr');
  if (errEl) errEl.remove();
}

export function openRoutineEdit(r = null) {
  clearRoutineError();
  rEdit = r ? r.id : null;
  const rName = document.getElementById('rName');
  const rType = document.getElementById('rType');
  const rVal = document.getElementById('rVal');
  const rDays = document.getElementById('rDays');
  const rSteps = document.getElementById('rSteps');
  const rtForm = document.getElementById('rtForm');

  if (rName) rName.value = r ? r.name : '';
  if (rType) rType.value = r ? r.type : 'manual';
  if (rVal) rVal.value = r ? (r.val || '') : '';
  if (rDays) rDays.value = r ? (r.days || 'all') : 'all';
  if (rSteps) rSteps.value = r ? (r.steps || '') : '';

  updateRoutineFormUI();
  if (rtForm) rtForm.style.display = 'block';
  if (rName) rName.focus();
}

export function saveRoutine() {
  clearRoutineError();
  const rName = document.getElementById('rName');
  const rType = document.getElementById('rType');
  const rVal = document.getElementById('rVal');
  const rDays = document.getElementById('rDays');
  const rSteps = document.getElementById('rSteps');
  const rtForm = document.getElementById('rtForm');

  const t = (rType && rType.value) || 'manual';
  let v = (rVal && rVal.value.trim()) || '';

  if (t === 'time') {
    const m = /^(\d{1,2})[:.](\d{2})$/.exec(v);
    if (!m || +m[1] > 23 || +m[2] > 59) {
      sfx.bad();
      showRoutineError('Saat 08:00 biçiminde olmalı');
      return;
    }
    v = pad2(+m[1]) + ':' + m[2];
  } else if (t !== 'manual' && !v) {
    sfx.bad();
    showRoutineError('Tetikleyici değeri boş olamaz');
    return;
  }

  const o = {
    id: rEdit || uniqueRecordId(routines, 'rt'),
    name: (rName && rName.value.trim()) || 'Unnamed routine',
    type: t,
    val: t === 'manual' ? '' : v,
    days: (rDays && rDays.value) || 'all',
    steps: (rSteps && rSteps.value.trim()) || '',
    on: 1
  };

  const previous = routines.slice();
  const i = routines.findIndex(x => x.id === o.id);
  if (i < 0) {
    routines.push(o);
  } else {
    ['on', 'last', 'ok'].forEach(k => {
      if (routines[i][k] !== undefined) o[k] = routines[i][k];
    });
    routines[i] = o;
  }

  renderRoutines();
  if (saveStoreCb && saveStoreCb({ emitSave: true }) === false) {
    routines.splice(0, routines.length, ...previous);
    renderRoutines();
    return;
  }
  sfx.ok();

  if (rtForm) rtForm.style.display = 'none';
}

export function routineResult(id, ok, options = {}) {
  const { emitSave = false } = options;
  const r = routines.find(x => x.id === id);
  if (!r) return;
  r.last = stamp();
  r.ok = ok !== false;
  renderRoutines();
  if (saveStoreCb) saveStoreCb({ emitSave });
}

export function setRoutines(list, options = {}) {
  const { emitSave = false, silent = false } = options;
  const rawList = Array.isArray(list) ? list : [];
  const result = validateAndNormalizeSnapshot({ routines: rawList });
  if (!result.ok) { logBridgeError('routines update', new Error(result.error)); return false; }
  routines = result.candidate.routines;
  renderRoutines();
  if (!silent && saveStoreCb) saveStoreCb({ emitSave });
}

export function initRoutines(options = {}) {
  // Empty default if no saved routines (removes mock data per Rule 6)
  const rawList = Array.isArray(options.initialRoutines) ? options.initialRoutines : [];
  routines = rawList
    .filter(r => r && typeof r === 'object' && !Array.isArray(r))
    .map(r => ({
      ...r,
      steps: normalizeSteps(r.steps)
    }));
  saveStoreCb = options.saveStore || null;

  const rtList = document.getElementById('rtList');
  if (rtList) {
    rtList.addEventListener('click', e => {
      const btn = e.target.closest('button, input');
      if (!btn || !btn.closest('.acts')) return;
      const acts = btn.closest('.acts');
      const id = acts.dataset.id;
      const r = routines.find(x => x.id === id);
      if (!r) return;

      const action = btn.dataset.a;
      if (action === 'on') {
        r.on = btn.checked ? 1 : 0;
        if (saveStoreCb) saveStoreCb({ emitSave: true });

        sfx.check();
      } else if (action === 'run') {
        runRoutine(r, 'manual');
      } else if (action === 'edit') {
        openRoutineEdit(r);
      } else if (action === 'del') {
        routines = routines.filter(x => x.id !== id);
        if (saveStoreCb) saveStoreCb({ emitSave: true });
        renderRoutines();
        sfx.del();

      }
    });
  }

  const rType = document.getElementById('rType');
  if (rType) rType.addEventListener('change', updateRoutineFormUI);

  const rNew = document.getElementById('rNew');
  if (rNew) rNew.addEventListener('click', () => openRoutineEdit(null));

  const rCancel = document.getElementById('rCancel');
  if (rCancel) {
    rCancel.addEventListener('click', () => {
      clearRoutineError();
      const form = document.getElementById('rtForm');
      if (form) form.style.display = 'none';
    });
  }

  const rSave = document.getElementById('rSave');
  if (rSave) rSave.addEventListener('click', saveRoutine);

  renderRoutines();
}
