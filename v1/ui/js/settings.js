/**
 * settings.js - Theme, devices, layout customization, profile, and backup management
 */

import { sfx, setSfxConfig } from './sfx.js';
import {initPermissions, refreshPermissions} from './permissions.js';
import { liveAudio } from './live_audio.js';
import { emit, logBridgeError, isBackendAvailable } from './api.js';
import { writeStoredJSON } from './storage.js';
import { canRestoreNativeNotes, restoreNativeNotes, setNotesImportLock } from './notes.js';
import { validateAndNormalizeSnapshot, sanitizeLayout, normalizeRoutineSteps } from './schema.js';
export { validateAndNormalizeSnapshot, validateSnapshot, sanitizeLayout, ALLOWED_WIDGET_IDS } from './schema.js';
import {initLayoutSettings, applyLayout, renderLayout, updateCompactView} from './layout.js';
export {applyLayout, renderLayout, updateCompactView} from './layout.js';
import {initDeviceSettings, setDevices, queryDevices} from './devices.js';
export {setDevices, queryDevices, getAudioDeviceId} from './devices.js';
import { S, DEF, getState, setState } from './reactor.js';


import {store, defaultInterfaceSettings} from './preferences.js';
export {store, defaultInterfaceSettings} from './preferences.js';

let collectionGetters = {
  getNotes: null,
  getSkills: null,
  getRoutines: null
};

export function registerCollectionGetters(getters = {}) {
  Object.assign(collectionGetters, getters);
}

let backupImportHandler = null;
// The native API remains synchronous; native requests are queued with their copies.
let pendingBackendSave = null;
let saveQueue = Promise.resolve();
let saveRevision = 0;
let importingBackup = false;
let memoryBase = {pMem: "", pMemory: false};
export function setBackupImportHandler(handler) {
  backupImportHandler = handler;
}

function saveStatus(message) {
  document.querySelectorAll('.save-status').forEach(label => { label.textContent = message; });
}

function queueSettingsSave(value) {
  const payload = JSON.parse(JSON.stringify({...value, memoryBase}));
  const native = isBackendAvailable(), revision = ++saveRevision;
  const observer = window.vex?.onSave || window.jarvis?.onSave;
  if (typeof observer === 'function') {
    try { Promise.resolve(observer(JSON.parse(JSON.stringify(payload)))).catch(error => logBridgeError('save observer', error)); }
    catch (error) { logBridgeError('save observer', error); }
  }
  saveStatus(native ? 'Saving settings…' : 'Saved in this browser');
  const send = () => emit('save', payload);
  const operation = native ? saveQueue.then(send, send) : send();
  // The wait limit does not cancel/repeat the actual request that is ongoing in the queue.
  // This way, the previous delayed record cannot overwrite a newer record.
  saveQueue = operation;
  pendingBackendSave = (async () => {
    let timer;
    try {
      const timeout = new Promise(resolve => {
        timer = setTimeout(() => resolve({ ok: false, unknown: true,
          error: new Error('Settings save was not confirmed in time. State is unknown; no automatic retry was made.') }), 12000);
      });
      const result = await Promise.race([operation, timeout]);
      if (result.response?.memory_base && JSON.stringify(memoryBase) === JSON.stringify(payload.memoryBase))
        memoryBase = result.response.memory_base;
      const confirmed = !native || (result.ok && result.response?.saved === true && result.response?.completed === true);
      if (native && result.ok && !confirmed) logBridgeError('save', new Error('Native settings save was not confirmed'));
      if (native && result.unknown) logBridgeError('save', result.error);
      if (revision === saveRevision) saveStatus(result.response?.code === 'memory_changed'
        ? 'Personal memory changed; restart the app before editing again'
        : confirmed ? (native ? 'Settings saved' : 'Saved in this browser') : 'Settings save not confirmed');
      return { ...result, confirmed };
    } finally { clearTimeout(timer); }
  })();
  return pendingBackendSave;
}

function rgb(s) {
  const m = s.match(/\d+/g);
  return m ? '#' + m.slice(0, 3).map(n => (+n).toString(16).padStart(2, '0')).join('') : s;
}

export function loadStoredData() {
  try {
    const raw = localStorage.getItem('taskvex_ui') || localStorage.getItem('jarvis_ui');
    const parsed = raw ? JSON.parse(raw) : {};
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('Invalid saved settings');
    let repaired = false;
    for (const [key, original] of Object.entries(parsed)) {
      let value = original;
      if (['notes', 'skills', 'routines'].includes(key) && Array.isArray(value)) {
        const valid = [], ids = new Set();
        for (let item of value) {
          if (key === 'routines' && item && typeof item === 'object') item = { ...item, steps: normalizeRoutineSteps(item.steps) };
          const result = validateAndNormalizeSnapshot({ [key]: [item] });
          const normalized = result.ok && result.candidate[key][0];
          if (!normalized || (normalized.id != null && ids.has(normalized.id))) { repaired = true; continue; }
          if (normalized.id != null) ids.add(normalized.id);
          valid.push(normalized);
        }
        value = valid;
      }
      const result = validateAndNormalizeSnapshot({ [key]: value });
      if (!result.ok) { repaired = true; continue; }
      for (const [field, normalized] of Object.entries(result.candidate)) {
        // Keep defaults for unavailable scalar settings; collections have explicit empty defaults.
        if (normalized != null) store[field] = normalized;
      }
    }
    if (repaired) logBridgeError('local storage recovery', new Error('Invalid saved fields were skipped; valid data was preserved'));
  } catch (error) { logBridgeError('local storage read', error); }
  store.layout = sanitizeLayout(store.layout);
  for (const key of ['notes', 'skills', 'routines']) if (!Array.isArray(store[key])) store[key] = [];
}

export function saveAll(options = {}) {
  const { emitSave = true } = options;

  if (collectionGetters.getNotes) store.notes = collectionGetters.getNotes();
  if (collectionGetters.getSkills) store.skills = collectionGetters.getSkills();
  if (collectionGetters.getRoutines) store.routines = collectionGetters.getRoutines();

  store.prof = store.prof || {};
  const p = store.prof;
  const pFields = [
    ['pLang', 'value'],
    ['pWake', 'value'],
    ['pBr', 'value'],
    ['pTab', 'checked'],
    ['pApp', 'checked'],
    ['pMemory', 'checked'],
    ['pLearn', 'checked'],
    ['pMemoryConfirm', 'checked'],
    ['pIns', 'value'],
    ['pMem', 'value'],
    ['pSc', 'value'],
    ['pSys', 'value'],
    ['pGreet', 'value']
  ];
  pFields.forEach(([i, k]) => {
    const el = document.getElementById(i);
    if (el) p[i] = el[k];
  });

  if (!p.pMemory || !p.pLearn || p.pMemoryConfirm === false) showMemoryProposal(null);

  store.devs = store.devs || {};
  const dIn = document.getElementById('dIn');
  const dOut = document.getElementById('dOut');
  const dCam = document.getElementById('dCam');
  // Native audio preference is owned by onchange/store. Pure scan default
  // Registry or interface reset should not create a new preference just because it shows the option.
  if (!isBackendAvailable() && dIn && dIn.options.length > 0 && dIn.value && dIn.value !== '-1') {
    store.devs.dIn = dIn.value;
  }
  if (!isBackendAvailable() && dOut && dOut.options.length > 0 && dOut.value && dOut.value !== '-1') {
    store.devs.dOut = dOut.value;
  }
  if (dCam && dCam.options.length > 0 && dCam.value && dCam.value !== '-1') {
    store.devs.dCam = dCam.value;
  }

  const sfxT = document.getElementById('sfxT');
  const volR = document.getElementById('volR');
  const wakeR = document.getElementById('wakeR');
  const thr = document.getElementById('thr');
  const onTop = document.getElementById('onTop');
  const cmpSel = document.getElementById('cmpSel');

  store.sfx = sfxT ? sfxT.checked : true;
  store.vol = volR ? +volR.value / 100 : 0.8;
  const replyVolR = document.getElementById('replyVolR');
  if (replyVolR) store.replyVolume = +replyVolR.value / 100;
  store.wake = wakeR ? +wakeR.value : 50;
  const sleepDelay = document.getElementById('sleepDelay');
  if (sleepDelay && sleepDelay.checkValidity()) store.sleepDelay = +sleepDelay.value;
  store.noise = thr ? +thr.value : 420;
  store.onTop = onTop ? onTop.checked : false;
  store.cmp = cmpSel ? cmpSel.value : 'auto';

  setSfxConfig(store.sfx, store.vol);
  liveAudio.setVolume(store.replyVolume);

  const mSel = document.getElementById('mSel');
  const vSel = document.getElementById('vSel');
  if (mSel && vSel) {
    const mVal = mSel.value;
    const vVal = vSel.value;
    store.conn = store.conn || {};
    const mOpt = mSel.options[mSel.selectedIndex];
    if (mVal && !mOpt?.disabled && !mVal.toLowerCase().startsWith('loading')) {
      store.conn.model = mVal;
    }
    const vOpt = vSel.options[vSel.selectedIndex];
    if (vVal && !vOpt?.disabled && !vVal.toLowerCase().startsWith('loading')) {
      store.conn.voice = vVal;
    }
  }

  if (!writeStoredJSON('taskvex_ui', store)) return false;

  if (emitSave) {
    queueSettingsSave(store);
  }
  return true;
}

export async function saveSettingsConfirmed() {
  // Browser mode retains the old native/fallback behavior. Modal in native mode,
  // It only closes when the write to disk is verified by the backend.
  if (!saveAll()) return false;
  if (!isBackendAvailable()) return true;
  return (await pendingBackendSave).confirmed;
}

export async function importBackup(parsed) {
  // Just take the backup areas that the UI has; such as catalog/telemetry/online
  // We do not represent external states as real data by restoring them from the backup file.
  if (importingBackup || !parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return false;
  const fields = new Set([...Object.keys(defaultInterfaceSettings()), 'devs', 'prof', 'conn', 'notes', 'skills', 'routines']);
  const owned = Object.fromEntries(Object.entries(parsed).filter(([key]) => fields.has(key)));
  if (!Object.keys(owned).length || !backupImportHandler) return false;
  const validation = validateAndNormalizeSnapshot(JSON.parse(JSON.stringify(owned)));
  if (!validation.ok) return false;
  const candidate = validation.candidate;
  for (const [key, value] of Object.entries(owned)) {
    if (!(key in candidate)) return false;
    if (['notes', 'skills', 'routines'].includes(key) && value !== null &&
        (!Array.isArray(value) || candidate[key]?.length !== value.length)) return false;
    if (['colors', 'devs', 'prof', 'conn'].includes(key) && JSON.stringify(value) !== JSON.stringify(candidate[key])) return false;
  }
  if (Array.isArray(owned.notes) && owned.notes.some(note => typeof note !== 'string' &&
      (!note || typeof note !== 'object' || !['string', 'number'].includes(typeof note.t) ||
       ![undefined, null, false, true, 0, 1].includes(note.d)))) return false;
  const hasNativeNotes = isBackendAvailable() && Object.hasOwn(owned, 'notes');
  if (hasNativeNotes && !canRestoreNativeNotes()) {
    saveStatus('Finish the notes transfer or current note operation before importing.');
    return false;
  }
  // The native annotation tool is more stringent; Check the entire file before writing settings.
  if (hasNativeNotes && (candidate.notes || []).some(n => !n.t.trim() || n.t.length > 10000 ||
      (n.id !== undefined && (typeof n.id !== 'string' || !n.id.trim())))) return false;
  if (hasNativeNotes) {
    const ids = (candidate.notes || []).map(n => n.id).filter(id => id !== undefined);
    if (new Set(ids).size !== ids.length) return false;
  }

  importingBackup = true;
  const controls = [...document.querySelectorAll('button, input, select, textarea')].map(element => [element, element.disabled]);
  setNotesImportLock(true);
  controls.forEach(([element]) => { element.disabled = true; });
  try {
    // First check if the existing local register is writable; import data yet
    // application. In case of native rejection/timeout, collections remain the same.
    if (!saveAll({ emitSave: false })) return false;
    const previous = JSON.parse(JSON.stringify(store));
    const native = isBackendAvailable();
    if (native && !(await queueSettingsSave({ ...previous, ...owned })).confirmed) return false;
    if (hasNativeNotes) {
      if (!(await restoreNativeNotes(candidate.notes || []))) {
        saveStatus('Settings saved; note restore was not confirmed. Check the notes status.');
        return false;
      }
      // Notes are now the backend result; local snapshot cannot rewrite them.
      delete candidate.notes;
      previous.notes = collectionGetters.getNotes();
    }
    if (backupImportHandler(candidate, { emitSave: false }) !== true) {
      // If localStorage setItem fails, previous bytes remain. Memory/DOM'u
      // undo without trying to write to the disk again; native registry is a separate repository.
      backupImportHandler(previous, { emitSave: false, skipPersist: true });
      saveStatus(native ? 'Settings saved; local backup import failed' : 'Backup import failed');
      logBridgeError('import', new Error(native ? 'Native settings and any restored notes were saved, but local backup data could not be stored. Backend notes remain authoritative.' : 'Local backup data could not be stored. Previous data was kept.'));
      return false;
    }
    if (!native) queueSettingsSave(store);
    saveStatus(native ? 'Backup imported; settings saved' : 'Backup imported in this browser');
    return true;
  } catch (error) {
    logBridgeError('import', error);
    return false;
  } finally {
    controls.forEach(([element, disabled]) => { element.disabled = disabled; });
    setNotesImportLock(false);
    importingBackup = false;
  }
}

export function marks() {
  const sw = document.getElementById('sw');
  if (!sw) return;
  [...sw.querySelectorAll('button')].forEach(b => {
    b.classList.toggle('a', rgb(b.style.background) === store.theme);
  });
}

export function paint() {
  const root = document.documentElement;
  root.style.setProperty('--gold', store.theme);
  root.style.setProperty('--c', S[getState()] ? S[getState()][1] : store.theme);
  root.style.setProperty('--ln', `color-mix(in srgb, ${store.theme} 26%, #141414)`);
  root.style.setProperty('--bg', `color-mix(in srgb, ${store.theme} 4.5%, #050403)`);
  root.style.setProperty('--mut', `color-mix(in srgb, ${store.theme} 36%, #78746c)`);

  Object.keys(S).forEach(k => {
    S[k][1] = store.colors[k] || (k === 'idle' ? store.theme : DEF[k]);
  });

  setState(getState(), true);
  marks();
}

export function switchTab(t) {
  if (!['theme', 'audio', 'connection', 'interface', 'system'].includes(t)) t = 'theme';
  document.querySelectorAll('#mSet .tp').forEach(p => p.classList.toggle('a', p.dataset.t === t));
  document.querySelectorAll('#setTabs .tab').forEach(b => b.classList.toggle('a', b.dataset.t === t));
  store.tab = t;
  if(t==='system')void refreshPermissions();
}

let memoryProposal = null;
let memoryDecisionBusy = false;

/** The candidate is shown alone; free model text is never a permanent record. */
export function showMemoryProposal(proposal) {
  memoryProposal = proposal;
  const panel = document.getElementById('memoryProposal');
  panel.hidden = !proposal;
  if (!proposal) return;
  document.getElementById('memoryProposalText').textContent = proposal.text;
  document.getElementById('memoryProposalSource').textContent = 'From this message: ' + proposal.source_quote;
  document.getElementById('memoryProposalStatus').textContent = 'Not saved. Review the fact before accepting.';
  for (const id of ['memoryAccept','memoryDismiss']) document.getElementById(id).disabled = false;
}

/** A delayed/old decision cannot hide a newer candidate. */
export function resolveMemoryProposal(id) {
  if (memoryProposal?.id === id) showMemoryProposal(null);
}

async function decideMemory(approve) {
  if (!memoryProposal || memoryDecisionBusy) return;
  memoryDecisionBusy = true;
  const id = memoryProposal.id, buttons = ['memoryAccept','memoryDismiss'].map(id => document.getElementById(id));
  buttons.forEach(b => {b.disabled = true;});
  try {
    const result = await emit('memory_decision', {request_id:crypto.randomUUID(), arguments:{id,approve}});
    if (memoryProposal?.id !== id) return;
    if (result.ok && result.response?.verified && result.response?.completed) {
      if (!applyMemoryProfile(result.response.memory_profile)) throw new Error('Profile refresh rejected');
      showMemoryProposal(null);
      saveStatus(approve ? 'Suggested fact saved' : 'Suggestion dismissed; memory unchanged');
    } else {
      document.getElementById('memoryProposalStatus').textContent = result.response?.unknown
        ? 'Result unknown. Reopen the app; do not retry.' : (result.response?.error || 'Suggestion was not saved');
      if (!result.response?.unknown && !result.unknown) {
        if (result.response?.completed) {
          const message = result.response.error || 'Suggestion expired; nothing saved';
          showMemoryProposal(null);saveStatus(message);
        } else buttons.forEach(b => {b.disabled = false;});
      }
    }
  } catch (error) {
    logBridgeError('memory decision', error);
    document.getElementById('memoryProposalStatus').textContent = 'Result unknown. Reopen the app; do not retry.';
  } finally {memoryDecisionBusy = false;}
}

/** Model result uses the same snapshot path; It does not delete the draft in the open form. */
export function applyMemoryProfile(profile) {
  const previous = store.prof || {}, base = memoryBase, drafts = [];
  for (const key of ['pLang','pWake','pBr','pIns','pMem','pSc','pSys','pGreet','pTab','pApp','pMemory','pLearn','pMemoryConfirm']) {
    const el = document.getElementById(key);
    if (!el) continue;
    const prop = el.type === 'checkbox' ? 'checked' : 'value';
    const before = previous[key] ?? (prop === 'checked' ? false : '');
    if (el[prop] !== before) drafts.push([el, prop, el[prop]]);
  }
  if (window.vex.loadStore({prof: profile}) !== true) return false;
  for (const [el, prop, value] of drafts) el[prop] = value;
  // If the draft is based on the old document, it does not gain the right to quietly crush the new text.
  if (drafts.some(([el]) => ['pMem','pMemory'].includes(el.id))) memoryBase = base;
  if (drafts.length) saveStatus('Saved memory refreshed; unsaved profile draft kept. Conflicts require restarting the app.');
  return true;
}

export function loadStore(o, options = {}) {
  if (o?.prof) memoryBase = {pMem: o.prof.pMem ?? "", pMemory: o.prof.pMemory === true};
  if (!o || typeof o !== 'object') return;
  const { emitSave = false, skipPersist = false } = options;
  [
    'theme',
    'colors',
    'devs',
    'prof',
    'sfx',
    'vol',
    'replyVolume',
    'conn',
    'notes',
    'skills',
    'layout',
    'cmp',
    'tab',
    'wake',
    'routines',
    'onTop',
    'noise',
    'sleepDelay'
  ].forEach(k => {
    if (o[k] != null) store[k] = o[k];
  });

  store.layout = sanitizeLayout(store.layout);

  paint();
  const custT = document.getElementById('custT');
  if (custT) custT.value = store.theme;
  marks();

  Object.keys(S).forEach(k => {
    const el = document.getElementById('c_' + k);
    if (el) el.value = S[k][1];
  });

  const P = store.prof || {};
  const review = document.getElementById('pMemoryConfirm');
  if (review) review.checked = P.pMemoryConfirm !== false;
  if (P.pMemory !== true || P.pLearn !== true || P.pMemoryConfirm === false) showMemoryProposal(null);
  ['pLang', 'pBr', 'pIns', 'pMem', 'pSc', 'pSys', 'pGreet', 'pWake'].forEach(i => {
    const el = document.getElementById(i);
    if (el && (P[i] != null || i === 'pMem')) el.value = P[i] ?? '';
  });
  ['pTab', 'pApp', 'pMemory', 'pLearn'].forEach(i => {
    const el = document.getElementById(i);
    if (el && (P[i] != null || ['pMemory','pLearn','pMemoryConfirm'].includes(i))) el.checked = P[i] === true;
  });

  const sfxT = document.getElementById('sfxT');
  const volR = document.getElementById('volR');
  const cmpSel = document.getElementById('cmpSel');
  const wakeR = document.getElementById('wakeR');
  const wv = document.getElementById('wv');
  const onTop = document.getElementById('onTop');
  const thr = document.getElementById('thr');
  const nv = document.getElementById('nv');
  const nth = document.getElementById('nth');

  const sleepDelay = document.getElementById('sleepDelay');
  if (sleepDelay) sleepDelay.value = store.sleepDelay ?? 10;
  if (sfxT) sfxT.checked = store.sfx !== false;
  if (volR) volR.value = (store.vol == null ? 0.8 : store.vol) * 100;
  const replyVolR = document.getElementById('replyVolR');
  const replyVolValue = document.getElementById('replyVolValue');
  if (replyVolR) replyVolR.value = Math.round(store.replyVolume * 100);
  if (replyVolValue) replyVolValue.textContent = Math.round(store.replyVolume * 100);
  liveAudio.setVolume(store.replyVolume);
  if (cmpSel) cmpSel.value = store.cmp || 'auto';
  if (wakeR) {
    wakeR.value = store.wake == null ? 50 : store.wake;
    if (wv) wv.textContent = wakeR.value;
  }
  if (onTop) onTop.checked = !!store.onTop;
  if (store.noise != null && thr) {
    thr.value = store.noise;
    if (nv) nv.textContent = store.noise;
    if (nth) nth.style.left = store.noise / 10 + '%';
  }

  setSfxConfig(store.sfx, store.vol);

  const mSel = document.getElementById('mSel');
  const vSel = document.getElementById('vSel');
  if (store.conn) {
    if (store.conn.model && mSel) mSel.value = store.conn.model;
    if (store.conn.voice && vSel) vSel.value = store.conn.voice;
  }

  applyLayout();
  renderLayout();
  updateCompactView();
  switchTab(store.tab || 'theme');

  if (!skipPersist) {
    if (!writeStoredJSON('taskvex_ui', store)) return false;

    if (emitSave) {
      queueSettingsSave(store);
    }
  }
  if (o.sleepDelay != null) window.dispatchEvent(new Event('taskvex-sleep-delay-changed'));
  if (o.noise != null) window.dispatchEvent(new Event('taskvex-noise-changed'));
}

export function initSettings(options = {}) {
  initPermissions();
  initDeviceSettings(saveAll);
  loadStoredData();
  setSfxConfig(store.sfx, store.vol);
  liveAudio.setVolume(store.replyVolume);

  // Settings tabs
  const setTabs = document.getElementById('setTabs');
  const TB = [
    ['theme', 'Theme'],
    ['audio', 'Audio'],
    ['connection', 'Connection'],
    ['interface', 'Interface'],
    ['system', 'System']
  ];
  if (setTabs) {
    setTabs.innerHTML = TB.map(t => `<button class="tab" data-t="${t[0]}">${t[1]}</button>`).join('');
    setTabs.addEventListener('click', e => {
      const btn = e.target.closest('.tab');
      if (btn) {
        sfx.blip();
        switchTab(btn.dataset.t);
      }
    });
  }
  switchTab(store.tab || 'theme');

  // Palette colors
  const sw = document.getElementById('sw');
  if (sw) {
    ['#e0b060', '#4fd8ff', '#5dffb0', '#ff5d5d', '#a78bfa'].forEach(c => {
      const b = document.createElement('button');
      b.style.background = c;
      b.addEventListener('click', () => {
        sfx.blip();
        store.theme = c;
        const ct = document.getElementById('custT');
        if (ct) ct.value = c;
        paint();
        marks();
        saveAll();
      });
      sw.append(b);
    });

    const ct = document.createElement('input');
    ct.type = 'color';
    ct.id = 'custT';
    ct.title = 'Custom color';
    ct.value = store.theme;
    ct.addEventListener('input', () => {
      store.theme = ct.value;
      paint();
      marks();
      saveAll();
    });
    sw.append(ct);
  }

  // State color rows
  const stCols = document.getElementById('stCols');
  if (stCols) {
    Object.keys(S).forEach(k => {
      const r = document.createElement('div');
      r.className = 'row';
      r.innerHTML = `<span>${S[k][0]}</span>`;

      const inp = document.createElement('input');
      inp.type = 'color';
      inp.id = 'c_' + k;
      inp.value = S[k][1] || DEF[k];
      inp.addEventListener('input', () => {
        store.colors[k] = inp.value;
        paint();
        setState(k);
      });

      const resetB = document.createElement('button');
      resetB.className = 'cb';
      resetB.textContent = 'Reset';
      resetB.addEventListener('click', () => {
        delete store.colors[k];
        paint();
        inp.value = S[k][1];
      });

      const wrap = document.createElement('span');
      wrap.style.cssText = 'display:flex;gap:8px;align-items:center';
      wrap.append(inp, resetB);
      r.append(wrap);
      stCols.append(r);


    });
  }

  // Audio settings

  const sfxT = document.getElementById('sfxT');
  if (sfxT) {
    sfxT.checked = store.sfx !== false;
    sfxT.addEventListener('change', () => {
      store.sfx = sfxT.checked;
      setSfxConfig(store.sfx, store.vol);
      saveAll();
    });
  }

  const volR = document.getElementById('volR');
  if (volR) {
    volR.value = (store.vol == null ? 0.8 : store.vol) * 100;
    volR.addEventListener('input', function () {
      store.vol = this.value / 100;
      setSfxConfig(store.sfx, store.vol);
    });
    volR.addEventListener('change', () => {
      sfx.blip();
      saveAll();
    });
  }

  const replyVolR = document.getElementById('replyVolR');
  const replyVolValue = document.getElementById('replyVolValue');
  if (replyVolR) {
    replyVolR.value = Math.round(store.replyVolume * 100);
    if (replyVolValue) replyVolValue.textContent = replyVolR.value;
    replyVolR.addEventListener('input', () => {
      store.replyVolume = +replyVolR.value / 100;
      liveAudio.setVolume(store.replyVolume);
      if (replyVolValue) replyVolValue.textContent = replyVolR.value;
    });
    replyVolR.addEventListener('change', () => saveAll());
  }

  const thr = document.getElementById('thr');
  const nv = document.getElementById('nv');
  const nth = document.getElementById('nth');
  if (thr) {
    thr.value = store.noise != null ? store.noise : 420;
    if (nv) nv.textContent = thr.value;
    if (nth) nth.style.left = thr.value / 10 + '%';
    thr.addEventListener('input', function () {
      store.noise = +this.value;
      if (nv) nv.textContent = this.value;
      if (nth) nth.style.left = this.value / 10 + '%';
      window.dispatchEvent(new Event('taskvex-noise-changed'));
    });
    thr.addEventListener('change', () => { sfx.blip(); saveAll(); });
  }

  const sleepDelay = document.getElementById('sleepDelay');
  if (sleepDelay) {
    sleepDelay.value = store.sleepDelay ?? 10;
    for (const [id, direction] of [['sleepLess', -1], ['sleepMore', 1]]) {
      document.getElementById(id)?.addEventListener('click', () => {
        if (!sleepDelay.checkValidity() || !sleepDelay.value) { sleepDelay.reportValidity(); return; }
        sleepDelay.value = Math.max(0, Math.min(300, +sleepDelay.value + direction));
        sfx.blip(); sleepDelay.dispatchEvent(new Event('change'));
      });
    }
    sleepDelay.addEventListener('change', () => {
      if (!sleepDelay.checkValidity()) { sleepDelay.reportValidity(); sleepDelay.value = store.sleepDelay; return; }
      store.sleepDelay = +sleepDelay.value; saveAll();
      window.dispatchEvent(new Event('taskvex-sleep-delay-changed'));
    });
  }
  const wakeR = document.getElementById('wakeR');
  const wv = document.getElementById('wv');
  if (wakeR) {
    wakeR.value = store.wake == null ? 50 : store.wake;
    if (wv) wv.textContent = wakeR.value;
    wakeR.addEventListener('input', function () {
      store.wake = +this.value;
      if (wv) wv.textContent = this.value;
    });
    wakeR.addEventListener('change', function () {
      sfx.blip();
      saveAll();
      // The new threshold is read from the saved setting at the next sleep entry.
    });
  }

  // Window always on top
  const onTop = document.getElementById('onTop');
  if (onTop) {
    onTop.checked = !!store.onTop;
    onTop.addEventListener('change', async function () {
      const previous = !!store.onTop, desired = this.checked;
      if (isBackendAvailable()) {
        this.disabled = true;
        const result = await emit('ontop', desired);
        this.disabled = false;
        if (!result.ok || result.response?.completed !== true || result.response?.onTop !== desired) {
          this.checked = previous;
          if (result.ok) logBridgeError('ontop', new Error('Window preference was not confirmed'));
          return;
        }
      }
      // The physical change is instantaneous; permanent preference is saved with the existing Save model.
      store.onTop = desired;
    });
  }

  // Layout editor
  initLayoutSettings(saveAll);

  // Compact mode selector
  const cmpSel = document.getElementById('cmpSel');
  if (cmpSel) {
    cmpSel.value = store.cmp || 'auto';
    cmpSel.addEventListener('change', () => {
      store.cmp = cmpSel.value;
      sfx.lay();
      updateCompactView();
      saveAll();
    });
  }
  window.addEventListener('resize', updateCompactView);

  // Backup export / import
  const expB = document.getElementById('expB');
  if (expB) {
    expB.addEventListener('click', async () => {
      expB.disabled = true;
      try {
        if (!await saveSettingsConfirmed()) return;
        const a = document.createElement('a');
        const url = URL.createObjectURL(new Blob([JSON.stringify(store, null, 2)], { type: 'application/json' }));
        a.href = url;
        a.download = 'vex-backup.json';
        a.click();
        // File dialog can be canceled: save download request as completed
        // We do not present it as . We then release the used Blob URL.
        saveStatus('Backup download requested');
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      } finally { expB.disabled = false; }
    });
  }

  const impB = document.getElementById('impB');
  const impF = document.getElementById('impF');
  if (impB && impF) {
    impB.addEventListener('click', () => impF.click());
    impF.addEventListener('change', e => {
      const f = e.target.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = async ev => {
        try {
          const parsed = JSON.parse(ev.target.result);
          if (await importBackup(parsed)) sfx.ok();
          else alert('Backup import was not completed. Check the save status and log before retrying.');
        } catch (err) {
          alert('Invalid backup file');
        } finally { impF.value = ''; }
      };
      reader.onerror = () => {
        logBridgeError('backup read', reader.error);
        saveStatus('Backup file could not be read');
        impF.value = '';
      };
      reader.readAsText(f);
    });
  }

  // Just reset the interface preferences without deleting the collection/profile keys.
  const resetAll = document.getElementById('resetAll');
  if (resetAll) {
    resetAll.addEventListener('click', async () => {
      if (!confirm('Reset interface preferences? Notes, skills, routines and profile will be kept.')) return;
      resetAll.disabled = true;
      try {
        let snapshot = defaultInterfaceSettings();
        if (isBackendAvailable()) {
          const result = await emit('reset');
          if (!result.ok) return;
          if (result.response?.completed !== true || result.response?.saved !== true || !result.response.snapshot) {
            logBridgeError('reset', new Error('Interface reset was not confirmed'));
            return;
          }
          snapshot = result.response.snapshot;
        }
        if (window.vex.loadStore(snapshot) !== true) {
          logBridgeError('reset', new Error('Interface defaults could not be applied locally'));
        }
      } finally { resetAll.disabled = false; }
    });
  }

  document.getElementById('memoryAccept').addEventListener('click', () => {sfx.blip();decideMemory(true);});
  document.getElementById('memoryDismiss').addEventListener('click', () => {sfx.blip();decideMemory(false);});
  // Load profile values into inputs
  const P = store.prof || {};
  const review = document.getElementById('pMemoryConfirm');
  if (review) review.checked = P.pMemoryConfirm !== false;
  if (P.pMemory !== true || P.pLearn !== true || P.pMemoryConfirm === false) showMemoryProposal(null);
  ['pLang', 'pBr', 'pIns', 'pMem', 'pSc', 'pSys', 'pGreet', 'pWake'].forEach(i => {
    const el = document.getElementById(i);
    if (P[i] != null && el) el.value = P[i];
  });
  ['pTab', 'pApp', 'pMemory', 'pLearn'].forEach(i => {
    const el = document.getElementById(i);
    if (el && (P[i] != null || ['pMemory','pLearn','pMemoryConfirm'].includes(i))) el.checked = P[i] === true;
  });

  paint();
  applyLayout();
  renderLayout();
  updateCompactView();

  window.saveAll = saveAll;
}
