/**
 * settings.js - Theme, devices, layout customization, profile, and backup management
 */

import { sfx, setSfxConfig } from './sfx.js';
import { emit, logBridgeError, isBackendAvailable } from './api.js';
import { writeStoredJSON } from './storage.js';
import { canRestoreNativeNotes, restoreNativeNotes, setNotesImportLock } from './notes.js';
import { validateAndNormalizeSnapshot, sanitizeLayout, LD, normalizeRoutineSteps } from './schema.js';
export { validateAndNormalizeSnapshot, validateSnapshot, sanitizeLayout, ALLOWED_WIDGET_IDS } from './schema.js';
import { S, DEF, getState, setState } from './reactor.js';

const DEBUG = false;

export function defaultInterfaceSettings() {
  // Her çağrıda yeni nesne: colors gibi değişebilir alanlar varsayılanı kirletmesin.
  return { theme: '#a78bfa', colors: {}, sfx: true, vol: 0.8, wake: 50,
    noise: 420, onTop: false, cmp: 'auto', tab: 'theme', layout: null };
}

export const store = { ...defaultInterfaceSettings(), devs: {}, prof: {}, conn: {} };

const SZ = [0.85, 1, 1.15];
const TT = {
  time: 'Time',
  system: 'System',
  timer: 'Timer & Stopwatch',
  weather: 'Weather',
  calendar: 'Calendar',
  remind: 'Reminders',
  notes: 'Notes',
  media: 'Media',
  net: 'Network',
  log: 'Skill Log'
};

let collectionGetters = {
  getNotes: null,
  getSkills: null,
  getRoutines: null
};

export function registerCollectionGetters(getters = {}) {
  Object.assign(collectionGetters, getters);
}

let backupImportHandler = null;
// Yerel API senkron kalır; native talepler kopyalarıyla sıraya alınır.
let pendingBackendSave = null;
let saveQueue = Promise.resolve();
let saveRevision = 0;
let importingBackup = false;
export function setBackupImportHandler(handler) {
  backupImportHandler = handler;
}

function saveStatus(message) {
  document.querySelectorAll('.save-status').forEach(label => { label.textContent = message; });
}

function queueSettingsSave(value) {
  const payload = JSON.parse(JSON.stringify(value));
  const native = isBackendAvailable(), revision = ++saveRevision;
  const observer = window.vex?.onSave || window.jarvis?.onSave;
  if (typeof observer === 'function') {
    try { Promise.resolve(observer(JSON.parse(JSON.stringify(payload)))).catch(error => logBridgeError('save observer', error)); }
    catch (error) { logBridgeError('save observer', error); }
  }
  saveStatus(native ? 'Saving settings…' : 'Saved in this browser');
  const send = () => emit('save', payload);
  const operation = native ? saveQueue.then(send, send) : send();
  // Bekleme sınırı kuyrukta devam eden gerçek isteği iptal etmez/tekrarlamaz.
  // Böylece geciken önceki kayıt daha yeni bir kaydın üstüne yazamaz.
  saveQueue = operation;
  pendingBackendSave = (async () => {
    let timer;
    try {
      const timeout = new Promise(resolve => {
        timer = setTimeout(() => resolve({ ok: false, unknown: true,
          error: new Error('Settings save was not confirmed in time. State is unknown; no automatic retry was made.') }), 12000);
      });
      const result = await Promise.race([operation, timeout]);
      const confirmed = !native || (result.ok && result.response?.saved === true && result.response?.completed === true);
      if (native && result.ok && !confirmed) logBridgeError('save', new Error('Native settings save was not confirmed'));
      if (native && result.unknown) logBridgeError('save', result.error);
      if (revision === saveRevision) saveStatus(confirmed ? (native ? 'Settings saved' : 'Saved in this browser') : 'Settings save not confirmed');
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
    ['pBr', 'value'],
    ['pTab', 'checked'],
    ['pApp', 'checked'],
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

  store.devs = store.devs || {};
  const dIn = document.getElementById('dIn');
  const dOut = document.getElementById('dOut');
  const dCam = document.getElementById('dCam');
  // Native ses tercihinin sahibi onchange/store'dur. Sırf tarama varsayılan
  // seçeneği gösterdi diye kayıt veya arayüz reset'i yeni tercih yazmamalı.
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
  store.wake = wakeR ? +wakeR.value : 50;
  store.noise = thr ? +thr.value : 420;
  store.onTop = onTop ? onTop.checked : false;
  store.cmp = cmpSel ? cmpSel.value : 'auto';

  setSfxConfig(store.sfx, store.vol);

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
  // Tarayıcı modu eski yerel/fallback davranışını korur. Native modda modal,
  // yalnız diske yazma backend tarafından doğrulandığında kapanır.
  if (!saveAll()) return false;
  if (!isBackendAvailable()) return true;
  return (await pendingBackendSave).confirmed;
}

export async function importBackup(parsed) {
  // Yalnız UI'ın sahip olduğu yedek alanlarını al; katalog/telemetri/online gibi
  // dış durumları yedek dosyasından geri yükleyerek gerçek veri gibi göstermeyiz.
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
  // Native not aracı daha katıdır; bütün dosyayı ayar yazımı öncesi denetle.
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
    // Önce mevcut yerel kaydın yazılabildiğini kontrol et; import verisini henüz
    // uygulama. Native ret/timeout durumunda koleksiyonlar aynı kalır.
    if (!saveAll({ emitSave: false })) return false;
    const previous = JSON.parse(JSON.stringify(store));
    const native = isBackendAvailable();
    if (native && !(await queueSettingsSave({ ...previous, ...owned })).confirmed) return false;
    if (hasNativeNotes) {
      if (!(await restoreNativeNotes(candidate.notes || []))) {
        saveStatus('Settings saved; note restore was not confirmed. Check the notes status.');
        return false;
      }
      // Notlar artık backend sonucu; yerel snapshot onları tekrar yazamaz.
      delete candidate.notes;
      previous.notes = collectionGetters.getNotes();
    }
    if (backupImportHandler(candidate, { emitSave: false }) !== true) {
      // localStorage setItem başarısızlığında önceki baytlar kalır. Bellek/DOM'u
      // da diske yeniden yazmayı denemeden geri al; native kayıt ayrı depodur.
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

export function applyLayout() {
  const aL = document.getElementById('asideL');
  const aR = document.getElementById('asideR');
  if (!aL || !aR || !store.layout) return;

  const n = { L: 0, R: 0 };
  store.layout.forEach(w => {
    const e = document.getElementById('w_' + w.id);
    if (!e) return;
    (w.c === 'L' ? aL : aR).append(e);
    e.style.display = w.on ? '' : 'none';
    e.style.zoom = SZ[w.sz] !== undefined ? SZ[w.sz] : 1;
    e.style.setProperty('--i', String(2 + (n[w.c]++)));
  });
}

export function renderLayout() {
  const listEl = document.getElementById('layList');
  if (!listEl || !store.layout) return;

  listEl.innerHTML = '';
  store.layout.forEach((w, i) => {
    const row = document.createElement('div');
    row.className = 'row';

    const span = document.createElement('span');
    span.style.flex = '1';
    span.textContent = TT[w.id] || w.id;

    const upBtn = document.createElement('button');
    upBtn.className = 'ib';
    upBtn.dataset.a = 'u';
    upBtn.dataset.i = String(i);
    upBtn.textContent = '↑';

    const downBtn = document.createElement('button');
    downBtn.className = 'ib';
    downBtn.dataset.a = 'd';
    downBtn.dataset.i = String(i);
    downBtn.textContent = '↓';

    const cSel = document.createElement('select');
    cSel.className = 'mini';
    cSel.dataset.a = 'c';
    cSel.dataset.i = String(i);

    const optL = document.createElement('option');
    optL.value = 'L';
    optL.textContent = 'Left';
    if (w.c === 'L') optL.selected = true;

    const optR = document.createElement('option');
    optR.value = 'R';
    optR.textContent = 'Right';
    if (w.c === 'R') optR.selected = true;
    cSel.append(optL, optR);

    const sSel = document.createElement('select');
    sSel.className = 'mini';
    sSel.dataset.a = 's';
    sSel.dataset.i = String(i);
    ['Small', 'Medium', 'Large'].forEach((label, j) => {
      const opt = document.createElement('option');
      opt.value = String(j);
      opt.textContent = label;
      if (w.sz === j) opt.selected = true;
      sSel.append(opt);
    });

    const chk = document.createElement('input');
    chk.type = 'checkbox';
    chk.dataset.a = 'o';
    chk.dataset.i = String(i);
    chk.checked = !!w.on;

    row.append(span, upBtn, downBtn, cSel, sSel, chk);
    listEl.append(row);
  });
}

function updateLayout() {
  sfx.lay();
  applyLayout();
  renderLayout();
  saveAll();
  emit('layout', store.layout);
}

export function updateCompactView() {
  const cmpSel = document.getElementById('cmpSel');
  const m = (cmpSel && cmpSel.value) || store.cmp || 'auto';
  document.body.classList.toggle(
    'compact',
    m === 'on' || (m === 'auto' && (window.innerWidth < 900 || window.innerHeight < 620))
  );
}

export function switchTab(t) {
  if (!['theme', 'audio', 'connection', 'interface', 'system'].includes(t)) t = 'theme';
  document.querySelectorAll('#mSet .tp').forEach(p => p.classList.toggle('a', p.dataset.t === t));
  document.querySelectorAll('#setTabs .tab').forEach(b => b.classList.toggle('a', b.dataset.t === t));
  store.tab = t;
}

let devQueryTimer = null;
let deviceQueryPending = false, deviceQueryRevision = 0, nativeDevicesScanned = false;

/** Browser cihaz kimliği ile eski Python donanım indeksini karıştırma.
 * Varsayılan açık seçimdir; kaybolan/seçilemeyen özel cihazda sessiz fallback yok.
 */
export function getAudioDeviceId(id) {
  const value = store.devs?.[id];
  if (value == null || value === '' || value === 'default') return '';
  if (typeof value !== 'string' || value === '-1') throw new Error('Choose an available audio device in Settings.');
  return value;
}

export function setDevices(data) {
  if (devQueryTimer) {
    clearTimeout(devQueryTimer);
    devQueryTimer = null;
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) return;
  const populate = (selId, list, kind) => {
    const s = document.getElementById(selId);
    if (!s) return;
    s.innerHTML = '';
    if (!list || !list.length) {
      s.innerHTML = '<option value="-1">No devices found</option>';
      return;
    }
    list.forEach(d => {
      if (!d || typeof d !== 'object') return;
      const o = document.createElement('option');

      // Metadata identification & Conflict Precedence:
      // A device entry can have either integer index or string deviceId.
      // If both index and deviceId are provided in a single entry:
      // Explicit Precedence Rule: Native hardware integer index takes precedence if valid integer.
      const hasIntIndex = d.index != null && (
        typeof d.index === 'number'
          ? Number.isInteger(d.index)
          : /^-?\d+$/.test(String(d.index).trim())
      );
      const hasDeviceId = d.deviceId != null && String(d.deviceId).trim() !== '';

      if (hasIntIndex) {
        const intIdx = typeof d.index === 'number' ? d.index : parseInt(String(d.index).trim(), 10);
        o.value = String(intIdx);
        o.dataset.devKind = 'index';
        o.dataset.devIndex = String(intIdx);
        o.textContent = d.name || d.label || `${kind} ${intIdx}`;
        s.append(o);
      } else if (hasDeviceId) {
        const strId = String(d.deviceId).trim();
        o.value = strId;
        o.dataset.devKind = 'deviceId';
        o.dataset.deviceId = strId;
        o.textContent = d.name || d.label || `${kind} (${strId})`;
        s.append(o);
      }
    });
    if (store.devs && store.devs[selId] != null) {
      const target = String(store.devs[selId]);
      if ([...s.options].some(o => o.value === target)) {
        s.value = target;
      } else if (isBackendAvailable() && ['dIn', 'dOut'].includes(selId)) {
        // Kayıtlı cihaz kaybolduysa ilk cihazı seçilmiş gibi gösterme.
        const missing = new Option('Saved device unavailable — choose a device', target, true, true);
        missing.disabled = true;
        s.append(missing);
        s.value = target;
      }
    }
    s.onchange = () => {
      store.devs = store.devs || {};
      store.devs[selId] = s.value;
      sfx.blip();
      const selectedOpt = s.options[s.selectedIndex];
      if (!selectedOpt) return;

      const devKind = selectedOpt.dataset.devKind;
      if (isBackendAvailable() && ['dIn', 'dOut'].includes(selId)) {
        const message = document.getElementById('devMsg');
        const saved = saveAll({emitSave:false});
        if (message) message.textContent = saved
          ? 'Selection cached; applies to the next recording / Live reply. Save Settings to persist in desktop storage.'
          : 'Device preference could not be saved; check storage before restarting.';
        return;
      }
      let intIndex = null;
      let devId = null;

      if (devKind === 'index') {
        intIndex = parseInt(selectedOpt.dataset.devIndex, 10);
        devId = null;
      } else if (devKind === 'deviceId') {
        intIndex = null;
        devId = selectedOpt.dataset.deviceId;
      }

      emit('device', {
        id: selId,
        index: intIndex,
        deviceId: devId,
        label: selectedOpt?.text || ''
      });
    };
  };

  if ('inputs' in data) populate('dIn', data.inputs, 'Microphone');
  if ('outputs' in data) populate('dOut', data.outputs, 'Speaker');
  if ('cameras' in data) populate('dCam', data.cameras, 'Camera');

  if (data.currentIn != null && document.getElementById('dIn')) {
    document.getElementById('dIn').value = data.currentIn;
  }
  if (data.currentOut != null && document.getElementById('dOut')) {
    document.getElementById('dOut').value = data.currentOut;
  }
  if (data.currentCam != null && document.getElementById('dCam')) {
    document.getElementById('dCam').value = data.currentCam;
  }

  const devMsg = document.getElementById('devMsg');
  if (devMsg) devMsg.textContent = '';
}

export async function queryDevices() {
  if (isBackendAvailable()) {
    if (deviceQueryPending) return;
    const revision = ++deviceQueryRevision;
    deviceQueryPending = true;
    const message = document.getElementById('devMsg');
    if (message) message.textContent = 'Refreshing audio devices…';
    try {
      // Listeleme izin veya kayıt başlatmaz. İzin yalnız Mic düğmesinden gelir;
      // izin sonrası aynı fonksiyon adları/cihazları yeniden listeler.
      const devices = await navigator.mediaDevices.enumerateDevices();
      if (revision !== deviceQueryRevision) return;
      const list = kind => [{deviceId:'default', name:'System default'}, ...devices
        .filter(d => d.kind === kind && d.deviceId && d.deviceId !== 'default')
        .map((d, i) => ({deviceId:d.deviceId, name:d.label || `Audio device ${i + 1}`}))];
      setDevices({inputs:list('audioinput'), outputs:list('audiooutput')});
      nativeDevicesScanned = true;
      if (message) message.textContent = 'Audio devices listed automatically. If names are hidden, enable the microphone once to grant permission. Camera is not connected.';
    } catch {
      if (revision === deviceQueryRevision && message)
        message.textContent = 'Audio devices unavailable or permission denied. Existing preferences were kept.';
    } finally {
      if (revision === deviceQueryRevision) {
        deviceQueryPending = false;
      }
    }
    return;
  }
  const devMsg = document.getElementById('devMsg');
  if (devMsg) devMsg.textContent = 'Scanning…';
  if (devQueryTimer) {
    clearTimeout(devQueryTimer);
    devQueryTimer = null;
  }

  try {
    const res = await emit('query_devices');
    if (!res || !res.ok) {
      if (devMsg) devMsg.textContent = 'Backend yok, cihazlar taranamadı';
      return;
    }
    devQueryTimer = setTimeout(() => {
      devQueryTimer = null;
      if (devMsg) devMsg.textContent = 'Cihaz listesi gelmedi';
    }, 10000);
  } catch {
    if (devMsg) devMsg.textContent = 'Backend yok, cihazlar taranamadı';
  }
}

if (typeof window !== 'undefined') window.addEventListener('pagehide', () => { deviceQueryRevision++; });
if (typeof navigator !== 'undefined') navigator.mediaDevices?.addEventListener?.('devicechange', () => {
  if (nativeDevicesScanned) queryDevices();
});

export function loadStore(o, options = {}) {
  if (!o || typeof o !== 'object') return;
  const { emitSave = false, skipPersist = false } = options;
  [
    'theme',
    'colors',
    'devs',
    'prof',
    'sfx',
    'vol',
    'conn',
    'notes',
    'skills',
    'layout',
    'cmp',
    'tab',
    'wake',
    'routines',
    'onTop',
    'noise'
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
  ['pLang', 'pBr', 'pIns', 'pMem', 'pSc', 'pSys', 'pGreet'].forEach(i => {
    const el = document.getElementById(i);
    if (P[i] != null && el) el.value = P[i];
  });
  ['pTab', 'pApp'].forEach(i => {
    const el = document.getElementById(i);
    if (P[i] != null && el) el.checked = !!P[i];
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

  if (sfxT) sfxT.checked = store.sfx !== false;
  if (volR) volR.value = (store.vol == null ? 0.8 : store.vol) * 100;
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
}

export function initSettings(options = {}) {
  loadStoredData();
  setSfxConfig(store.sfx, store.vol);

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
  const demo = document.getElementById('demo');
  if (stCols && demo) {
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

      if (DEBUG) {
        const dBtn = document.createElement('button');
        dBtn.className = 'cb';
        dBtn.textContent = '▶ ' + S[k][0];
        dBtn.addEventListener('click', () => setState(k));
        demo.append(dBtn);
      }
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

  const thr = document.getElementById('thr');
  const nv = document.getElementById('nv');
  const nth = document.getElementById('nth');
  if (thr) {
    thr.value = store.noise != null ? store.noise : 420;
    if (nv) nv.textContent = thr.value;
    if (nth) nth.style.left = thr.value / 10 + '%';
    let noiseDebounceTimer = null;
    thr.addEventListener('input', function () {
      const th = +this.value;
      if (nv) nv.textContent = th;
      if (nth) nth.style.left = th / 10 + '%';
      clearTimeout(noiseDebounceTimer);
      noiseDebounceTimer = setTimeout(() => {
        emit('noise', th);
      }, 150);
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
      emit('wake_sens', +this.value);
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
      // Fiziksel değişim anlıktır; kalıcı tercih mevcut Save modeliyle kaydedilir.
      store.onTop = desired;
    });
  }

  // Layout editor
  const layList = document.getElementById('layList');
  if (layList) {
    layList.addEventListener('click', e => {
      const btn = e.target.closest('button');
      if (!btn) return;
      const L = store.layout;
      const i = +btn.dataset.i;
      const w = L[i];
      const d = btn.dataset.a === 'u' ? -1 : 1;
      let j = i + d;
      while (L[j] && L[j].c !== w.c) j += d;
      if (!L[j]) return;
      const t = L[i];
      L[i] = L[j];
      L[j] = t;
      updateLayout();
    });

    layList.addEventListener('change', e => {
      const t = e.target;
      const w = store.layout[+t.dataset.i];
      if (t.dataset.a === 'c') w.c = t.value;
      if (t.dataset.a === 's') w.sz = +t.value;
      if (t.dataset.a === 'o') w.on = t.checked ? 1 : 0;
      updateLayout();
    });
  }

  const layReset = document.getElementById('layReset');
  if (layReset) {
    layReset.addEventListener('click', () => {
      store.layout = JSON.parse(JSON.stringify(LD));
      updateLayout();
    });
  }

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
        // Dosya diyaloğu iptal edilebilir: indirme isteğini tamamlanmış kayıt
        // diye sunmayız. Kullanılan Blob URL'sini daha sonra serbest bırakırız.
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

  // Koleksiyon/profil anahtarlarını silmeden yalnız arayüz tercihlerini sıfırla.
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

  // Load profile values into inputs
  const P = store.prof || {};
  ['pLang', 'pBr', 'pIns', 'pMem', 'pSc', 'pSys', 'pGreet'].forEach(i => {
    const el = document.getElementById(i);
    if (P[i] != null && el) el.value = P[i];
  });
  ['pTab', 'pApp'].forEach(i => {
    const el = document.getElementById(i);
    if (P[i] != null && el) el.checked = !!P[i];
  });

  paint();
  applyLayout();
  renderLayout();
  updateCompactView();

  window.saveAll = saveAll;
}
