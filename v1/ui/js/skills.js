/**
 * skills.js - Native skill definitions and editor; There is no backend player yet.
 */

import { sfx } from './sfx.js';
import { logBridgeError } from './api.js';
import { validateSkillSteps, uniqueRecordId, validateAndNormalizeSnapshot, foldTr } from './schema.js';
import { showM } from './panels.js';

let skills = [];
let editId = null;
let saveStoreCb = null;
let openModalCb = null;
let closeModalCb = null;

function slugify(s) {
  return foldTr(s).replace(/[^a-z0-9_]+/g, '_').replace(/^_+|_+$/g, '');
}

export function getSkills() {
  return skills;
}

function createStatElement(s) {
  const statDiv = document.createElement('div');
  statDiv.className = 'sub';
  statDiv.style.margin = '0 0 8px';

  const runsNum = Number(s && s.runs);
  const runs = Number.isFinite(runsNum) ? Math.max(0, Math.floor(runsNum)) : 0;
  if (!runs) {
    statDiv.textContent = 'Not run yet';
    return statDiv;
  }

  const okNum = Number(s && s.ok);
  const ok = Number.isFinite(okNum) ? Math.max(0, Math.floor(okNum)) : 0;
  const pct = Math.round((100 * ok) / runs);
  const lastTxt = typeof s.last === 'string' ? s.last : (s.last != null ? String(s.last) : '—');

  statDiv.style.color = 'var(--gold)';
  statDiv.textContent = `${runs} runs · ${pct}% success · last: ${lastTxt}`;
  return statDiv;
}

export function renderSkills() {
  const container = document.getElementById('skList');
  if (!container) return;

  container.innerHTML = '';
  if (!skills || skills.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'sub';
    empty.textContent = 'No skills yet.';
    container.append(empty);
    return;
  }

  skills.forEach(s => {
    const card = document.createElement('div');
    card.className = 'sk';

    const titleWrap = document.createElement('div');
    const b = document.createElement('b');
    b.textContent = s.name || 'Unnamed skill';
    const trig = document.createElement('span');
    trig.className = 'sub';
    trig.textContent = ' · ' + (s.trigger || 'no trigger');
    titleWrap.append(b, trig);

    const desc = document.createElement('div');
    desc.className = 'sub';
    desc.textContent = s.desc || s.description || '';

    const stat = createStatElement(s);

    const acts = document.createElement('div');
    acts.className = 'acts';
    acts.dataset.id = s.id;

    const runB = document.createElement('button');
    runB.className = 'cb';
    runB.dataset.a = 'run';
    runB.textContent = '▶ Run';

    const editB = document.createElement('button');
    editB.className = 'cb';
    editB.dataset.a = 'edit';
    editB.textContent = 'Edit';

    const delB = document.createElement('button');
    delB.className = 'cb red';
    delB.dataset.a = 'del';
    delB.textContent = 'Delete';

    acts.append(runB, editB, delB);
    card.append(titleWrap, desc, stat, acts);
    container.append(card);
  });
}

export function runSkill(s) {
  if (s) alert('Skill execution is not connected yet. Your definition is saved locally.');
}

export function openSkillEdit(s = null) {
  editId = s ? s.id : null;
  const sName = document.getElementById('sName');
  const sTrig = document.getElementById('sTrig');
  const sParams = document.getElementById('sParams');
  const sDesc = document.getElementById('sDesc');
  const sSteps = document.getElementById('sSteps');
  const skForm = document.getElementById('skForm');

  if (sName) sName.value = s ? s.name : '';
  if (sTrig) sTrig.value = s ? (s.trigger || s.app_name || '') : '';
  if (sParams) {
    sParams.value = s ? (Array.isArray(s.params) ? s.params.join(', ') : (s.params || '')) : '';
  }
  if (sDesc) sDesc.value = s ? (s.desc || s.description || '') : '';

  let stepsVal = '';
  if (s) {
    if (typeof s.steps === 'string') {
      try {
        stepsVal = JSON.stringify(JSON.parse(s.steps), null, 2);
      } catch (e) {
        stepsVal = s.steps;
      }
    } else if (Array.isArray(s.steps)) {
      stepsVal = JSON.stringify(s.steps, null, 2);
    }
  }

  if (sSteps) {
    sSteps.value = stepsVal || '[\n  {\n    "step_type": "open_app",\n    "target": ""\n  }\n]';
  }

  if (skForm) skForm.style.display = 'block';
  if (sName) sName.focus();
}

export function saveSkill() {
  const sName = document.getElementById('sName');
  const sTrig = document.getElementById('sTrig');
  const sParams = document.getElementById('sParams');
  const sDesc = document.getElementById('sDesc');
  const sSteps = document.getElementById('sSteps');
  const skForm = document.getElementById('skForm');

  const nameVal = (sName && sName.value.trim()) || 'Unnamed skill';
  const trigVal = (sTrig && sTrig.value.trim()) || '';
  const descVal = (sDesc && sDesc.value.trim()) || '';
  const rawParams = (sParams && sParams.value.split(',').map(x => x.trim()).filter(Boolean)) || [];

  let parsedSteps = [];
  try {
    const rawSteps = (sSteps && sSteps.value.trim()) || '[]';
    parsedSteps = JSON.parse(rawSteps);
  } catch (e) {
    alert('Steps must be valid JSON!\nError: ' + e.message);
    return;
  }

  const stepsError = validateSkillSteps(parsedSteps);
  if (stepsError) {
    alert(stepsError);
    return;
  }

  // Prevent new skills from overwriting existing skills with the same name
  let sId = editId;
  if (!sId) {
    const baseSlug = slugify(nameVal) || 'sk';
    sId = baseSlug;
    let suffix = 1;
    while (skills.some(x => x.id === sId)) sId = `${baseSlug}_${suffix++}`;
  }

  const o = {
    id: sId,
    skill_name: nameVal,
    name: nameVal,
    trigger: trigVal,
    app_name: trigVal,
    params: rawParams,
    parameters: rawParams,
    desc: descVal,
    description: descVal,
    steps: parsedSteps,
    stepCount: parsedSteps.length
  };

  const previous = skills.slice();
  const i = skills.findIndex(x => x.id === o.id);
  if (i < 0) {
    skills.push(o);
  } else {
    ['runs', 'ok', 'last'].forEach(k => {
      if (skills[i][k] !== undefined) o[k] = skills[i][k];
    });
    skills[i] = o;
  }

  renderSkills();
  if (saveStoreCb && saveStoreCb({ emitSave: true }) === false) {
    skills.splice(0, skills.length, ...previous);
    renderSkills();
    return;
  }
  sfx.ok();

  if (skForm) skForm.style.display = 'none';
}

export function deleteSkill(id) {
  skills = skills.filter(x => x.id !== id);
  renderSkills();
  if (saveStoreCb) saveStoreCb({ emitSave: true });
  sfx.del();

}

export function setSkills(list, options = {}) {
  const emitSave = !!options.emitSave;
  const silent = !!options.silent;
  const rawList = Array.isArray(list) ? list : [];
  const result = validateAndNormalizeSnapshot({ skills: rawList });
  if (!result.ok) { logBridgeError('skills update', new Error(result.error)); return false; }
  skills = result.candidate.skills;
  renderSkills();
  if (!silent && saveStoreCb) saveStoreCb({ emitSave });
}

export function addSkill(o, options = {}) {
  if (!o || typeof o !== 'object' || Array.isArray(o)) return;
  const { emitSave = false, silent = false } = options;
  if (o.id != null && skills.some(s => String(s.id) === String(o.id))) return false;
  o = { ...o, id: o.id != null ? String(o.id) : uniqueRecordId(skills, 'sk') };
  const result = validateAndNormalizeSnapshot({ skills: [o] });
  if (!result.ok) { logBridgeError('skill add', new Error(result.error)); return false; }
  o = result.candidate.skills[0];
  skills.push(o);
  renderSkills();
  if (!silent && saveStoreCb) saveStoreCb({ emitSave });
  showM('mSkill');
  openSkillEdit(o);
}

export function skillResult(id, ok, options = {}) {
  const { emitSave = false, silent = false } = options;
  const s = skills.find(x => x.id === id);
  if (!s) return;
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  s.runs = (s.runs || 0) + 1;
  if (ok !== false) s.ok = (s.ok || 0) + 1;
  s.last = `${pad(d.getDate())}.${pad(d.getMonth() + 1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  renderSkills();
  if (!silent && saveStoreCb) saveStoreCb({ emitSave });
}

export function initSkills(options = {}) {
  const rawList = Array.isArray(options.initialSkills) ? options.initialSkills : [];
  skills = rawList
    .filter(s => s && typeof s === 'object' && !Array.isArray(s))
    .map(s => ({ ...s }));
  saveStoreCb = options.saveStore || null;
  openModalCb = options.openModal || null;
  closeModalCb = options.closeModal || null;

  const skList = document.getElementById('skList');
  if (skList) {
    skList.addEventListener('click', e => {
      const btn = e.target.closest('button');
      if (!btn) return;
      const acts = btn.closest('.acts');
      if (!acts) return;
      const id = acts.dataset.id;
      const s = skills.find(x => x.id === id);

      if (btn.dataset.a === 'run') runSkill(s);
      if (btn.dataset.a === 'edit') openSkillEdit(s);
      if (btn.dataset.a === 'del') deleteSkill(id);
    });
  }

  const skNew = document.getElementById('skNew');
  if (skNew) skNew.addEventListener('click', () => openSkillEdit(null));

  const skCancel = document.getElementById('skCancel');
  if (skCancel) {
    skCancel.addEventListener('click', () => {
      const form = document.getElementById('skForm');
      if (form) form.style.display = 'none';
    });
  }

  const skSave = document.getElementById('skSave');
  if (skSave) skSave.addEventListener('click', saveSkill);


  renderSkills();
}
