/**
 * connections.js - Model/voice catalog, Google account, telemetry, weather, network, media
 */

import { sfx } from './sfx.js';
import { emit, isBackendAvailable, sanitizeError, createPendingOperation } from './api.js';
import { store } from './settings.js';

let isPlayingMedia = false;
let calEvents = [];
let warnedHighApi = false;
let saveStoreCb = null;
let addTimelineCb = null;
let logMessageCb = null;
let locConfirmedValue = '';
const locOperation = createPendingOperation(() => {
  const message = document.getElementById('locMsg');
  if (message) message.textContent = 'Location status unknown. Press Set or Auto to check; the request will not be repeated.';
});

async function checkLocationStatus() {
  const id = locOperation.begin();
  const message = document.getElementById('locMsg');
  if (message) message.textContent = 'Checking location status…';
  const result = await emit('query_location');
  if (!locOperation.isCurrent(id)) return;
  if (!result.ok) { locOperation.markUnknown(); return; }
  const status = result.response;
  if (status?.pending === false && typeof status.saved === 'boolean') setLocationStatus(status);
}

export function setLocationStatus(data, { emitSave = false } = {}) {
  const locMsg = document.getElementById('locMsg');
  const locIn = document.getElementById('locIn');
  if (!data) return;

  if (typeof data === 'string') {
    locOperation.finish();
    if (locMsg) locMsg.textContent = 'Location status: ' + sanitizeError(data);
    return;
  }

  const failed = typeof data === 'object' && (data.saved === false || data.ok === false);
  const completed = typeof data === 'object' && (data.saved === true || data.completed === true);
  if (!failed && !completed) return;
  locOperation.finish();

  if (failed) {
    if (locMsg) locMsg.textContent = 'Failed to save location: ' + sanitizeError(data.error || 'Rejected by backend');
    return;
  }

  if (completed) {
    const name = data.name || locConfirmedValue || (locIn && locIn.value) || '';
    locConfirmedValue = name;
    if (locMsg) locMsg.textContent = 'Manual location saved: ' + name;
    if (locIn && name) locIn.value = name;
    if (saveStoreCb) saveStoreCb({ emitSave });
  }
}

export function setCatalog(cat) {
  if (!cat) return;

  const ms = document.getElementById('mSel');
  if (ms && Array.isArray(cat.models)) {
    ms.innerHTML = '';
    cat.models.forEach(m => {
      const o = document.createElement('option');
      o.value = m.id;
      o.textContent = (m.live ? '● [LIVE] ' : '✦ ') + m.name + (m.desc ? ' (' + m.desc.slice(0, 45) + '…)' : '');
      ms.append(o);
    });
    ms.disabled = !cat.models.length;
    if (!cat.models.length) ms.append(new Option('No models available', '', true, true));

    let chosenModel = null;
    if (cat.currentModel && cat.models.some(m => m.id === cat.currentModel)) {
      chosenModel = cat.currentModel;
    } else if (store.conn && store.conn.model && cat.models.some(m => m.id === store.conn.model)) {
      chosenModel = store.conn.model;
    } else if (cat.models.length > 0) {
      chosenModel = cat.models[0].id;
    }

    if (chosenModel) {
      ms.value = chosenModel;
      store.conn = store.conn || {};
      store.conn.model = chosenModel;
    }
    window.dispatchEvent(new CustomEvent('taskvex-live-model-ready', {detail:{ready:!!chosenModel}}));
  }

  const vs = document.getElementById('vSel');
  if (vs && Array.isArray(cat.voices)) {
    vs.innerHTML = '';
    cat.voices.forEach(v => {
      const o = document.createElement('option');
      o.value = v.id;
      o.textContent = v.name + (v.persona ? ' (' + v.persona + ')' : '') + (v.gender ? ' [' + v.gender + ']' : '');
      vs.append(o);
    });
    vs.disabled = !cat.voices.length;
    if (!cat.voices.length) vs.append(new Option('No voices available', '', true, true));

    let chosenVoice = null;
    if (cat.currentVoice && cat.voices.some(v => v.id === cat.currentVoice)) {
      chosenVoice = cat.currentVoice;
    } else if (store.conn && store.conn.voice && cat.voices.some(v => v.id === store.conn.voice)) {
      chosenVoice = store.conn.voice;
    } else if (cat.voices.length > 0) {
      chosenVoice = cat.voices[0].id;
    }

    if (chosenVoice) {
      vs.value = chosenVoice;
      store.conn = store.conn || {};
      store.conn.voice = chosenVoice;
    }
  }
}

let gConnTimer = null;

export function setGoogleStatus(st) {
  if (gConnTimer) {
    clearTimeout(gConnTimer);
    gConnTimer = null;
  }
  const gConnB = document.getElementById('gConnB');
  if (gConnB) gConnB.disabled = false;

  const e = document.getElementById('gConnStatus');
  if (!e || !st) return;

  if (st.connected) {
    e.textContent = 'Connected: ' + (st.email || 'Google Account');
    e.style.color = 'var(--gold)';
  } else {
    e.textContent = st.error ? 'Error: ' + sanitizeError(st.error) : 'Not Connected';
    e.style.color = '#ff5d5d';
  }
}

export function setWeather(o) {
  if (o === undefined) return;
  if (o === null) o = {};
  const wT = document.getElementById('wT');
  const wD = document.getElementById('wD');
  const wM = document.getElementById('wM');

  if (wT) wT.textContent = o.temp != null ? Math.round(o.temp) + '°' : '—°';

  if (wD) {
    const desc = [o.place, o.desc].filter(Boolean).join(' · ');
    wD.textContent = desc || 'Awaiting data';
  }

  if (wM) {
    const m = [];
    if (o.feels != null) m.push('Feels like ' + Math.round(o.feels) + '°');
    if (o.hum != null) m.push('Humidity ' + Math.round(o.hum) + '%');
    if (o.wind != null) m.push('Wind ' + Math.round(o.wind) + ' km/h');
    wM.textContent = m.join(' · ');
  }
}

export function setCalendar(events) {
  calEvents = Array.isArray(events) ? events.filter(e => e && typeof e === 'object') : [];
  const calN = document.getElementById('calN');
  const calL = document.getElementById('calL');

  if (calN) {
    calN.textContent = events ? String(calEvents.length) : '—';
  }

  if (calL) {
    calL.innerHTML = '';
    if (!calEvents.length) {
      calL.textContent = 'No events on your calendar today.';
      return;
    }

    calEvents.forEach(e => {
      const row = document.createElement('div');
      row.className = 'ev';
      if (e.t) {
        const b = document.createElement('b');
        b.textContent = e.t;
        row.append(b, document.createTextNode(' '));
      }
      row.append(document.createTextNode(e.s || ''));
      calL.append(row);
    });
  }
}

export function setReminders(reminders) {
  const remList = (Array.isArray(reminders) ? reminders : [])
    .filter(x => x && (typeof x === 'object' || typeof x === 'string'))
    .map(x => (typeof x === 'string' ? { s: x } : x))
    .filter(x => x && !x.d);

  const remN = document.getElementById('remN');
  const remL = document.getElementById('remL');

  if (remN) {
    remN.textContent = reminders ? String(remList.length) : '—';
  }

  if (remL) {
    remL.innerHTML = '';
    if (!remList.length) {
      remL.textContent = 'No pending reminders.';
      return;
    }

    remList.forEach(e => {
      const row = document.createElement('div');
      row.className = 'ev';
      if (e.t) {
        const b = document.createElement('b');
        b.textContent = e.t;
        row.append(b, document.createTextNode(' '));
      }
      row.append(document.createTextNode(e.s || ''));
      remL.append(row);
    });
  }
}

// Undefined preserves a partial field; null explicitly clears it. Zero is valid.
export function setTelemetry(data) {
  const o = data === null ? Object.fromEntries(['cpu','gpu','ram','cpuT','gpuT','ramTxt','bat','disk','win'].map(k => [k,null])) : data;
  if (!o) return;
  for (const key of ['cpu', 'gpu', 'ram']) {
    if (o[key] === undefined) continue;
    const value = o[key];
    const valid = typeof value === 'number' && Number.isFinite(value);
    const label = document.getElementById(key), bar = document.getElementById(key + 'Bar');
    if (label) label.textContent = valid ? Math.round(value) + '%' : '—';
    if (bar) bar.style.width = (valid ? Math.min(100, Math.max(0, value)) : 0) + '%';
  }
  for (const key of ['cpu', 'gpu', 'ram']) {
    const value = o[key === 'ram' ? 'ramTxt' : key + 'T'];
    if (value === undefined) continue;
    const el = document.getElementById(key + 'T');
    if (!el) continue;
    const valid = key === 'ram' ? value != null : typeof value === 'number' && Number.isFinite(value);
    el.textContent = valid ? (key === 'ram' ? String(value) : Math.round(value) + '°C') : '—';
    el.className = valid && key !== 'ram' ? (value >= 85 ? 'h' : value >= 75 ? 'w' : '') : '';
  }
  for (const key of ['bat', 'disk', 'win']) {
    if (o[key] !== undefined) {
      const el = document.getElementById(key);
      if (el) el.textContent = o[key] == null ? '—' : String(o[key]);
    }
  }
}

export function setTokens(u, m, isEst) {
  const tokTxt = document.getElementById('tokTxt');
  const tokSub = document.getElementById('tokSub');
  const tokBar = document.getElementById('tokBar');

  if (u == null || m == null || m <= 0) {
    if (tokTxt) tokTxt.textContent = '— / —';
    if (tokSub) tokSub.textContent = 'Remaining: — · Used: —';
    if (tokBar) tokBar.style.width = '0%';
    return;
  }

  const rem = Math.max(0, m - u);
  const pct = Math.max(0, Math.min(100, Math.round((u / m) * 100)));

  if (tokTxt) {
    tokTxt.innerHTML = '';
    tokTxt.append(document.createTextNode(`${u.toLocaleString('en-US')} / ${m.toLocaleString('en-US')}`));
    if (isEst) {
      const small = document.createElement('small');
      small.style.cssText = 'color:var(--mut);font-size:10px';
      small.textContent = ' (Estimated)';
      tokTxt.append(small);
    }
  }

  if (tokSub) {
    const estLabel = isEst ? ' (Estimated)' : '';
    tokSub.textContent = `Used${estLabel}: ${u.toLocaleString('en-US')} / ${m.toLocaleString('en-US')} (${pct}%) · Remaining: ${rem.toLocaleString('en-US')}`;
  }

  if (tokBar) {
    tokBar.style.width = pct + '%';
  }
}

export function setMedia(o) {
  if (!o) return;
  const mTitle2 = document.getElementById('mTitle2');
  const mArt = document.getElementById('mArt');
  const eq = document.getElementById('eq');
  const mPlay = document.getElementById('mPlay');

  if (o.title != null && mTitle2) mTitle2.textContent = o.title || 'No track playing';
  if (o.artist != null && mArt) mArt.textContent = o.artist || '—';
  if (o.playing != null) {
    isPlayingMedia = !!o.playing;
    if (eq) eq.classList.toggle('on', isPlayingMedia);
    if (mPlay) mPlay.textContent = isPlayingMedia ? '⏸' : '⏯';
  }
}

export function setNetwork(data) {
  const o = data === null ? {ping:null,down:null,wifi:null,api:null} : data;
  if (!o) return;
  for (const [key, id, unit] of [['ping','nPing',' ms'],['down','nDown',' Mbps'],['wifi','nWifi','%'],['api','nApi',' ms']]) {
    if (o[key] === undefined) continue;
    const value = o[key];
    const valid = typeof value === 'number' && Number.isFinite(value);
    const el = document.getElementById(id);
    if (el) el.textContent = valid ? Math.round(value) + unit : '—';
    if (key === 'api') {
      if (valid && value > 1500 && !warnedHighApi) sfx.warn();
      warnedHighApi = valid && value > 1500;
      if (el) el.style.color = !valid ? '' : value > 1500 ? '#ff5d5d' : value > 800 ? '#ffb347' : '';
    }
  }
}

export function initConnections(options = {}) {
  saveStoreCb = options.saveStore || null;
  addTimelineCb = options.addTimeline || null;
  logMessageCb = options.logMessage || null;

  // Modeller yalnız açık düğme tıklamasıyla API'den yüklenir. Boş/hatalı katalog
  // sabit model adlarıyla doldurulmaz; katalog başarısı Live bağlantısı değildir.
  const refreshModels = document.getElementById('refreshModels');
  const catalogStatus = document.getElementById('liveCatalogStatus');
  const catalogOperation = createPendingOperation(() => {
    if (catalogStatus) catalogStatus.textContent = 'Catalog result unknown. Reopen the app before loading again.';
  }, 65000);
  refreshModels?.addEventListener('click', async () => {
    if (catalogOperation.pending || catalogOperation.uncertain) return;
    if (!isBackendAvailable()) {
      catalogStatus.textContent = 'Live model loading requires the desktop app.';
      return;
    }
    const revision = catalogOperation.begin();
    refreshModels.disabled = true;
    setCatalog({ models: [] });
    catalogStatus.textContent = 'Loading Live models from Gemini API…';
    const result = await emit('query_catalog');
    if (!catalogOperation.isCurrent(revision)) return;
    catalogOperation.finish();
    refreshModels.disabled = false;
    if (!result.ok || result.response?.completed !== true || !Array.isArray(result.response.models)) {
      catalogStatus.textContent = sanitizeError(result.error || result.response?.error || 'Catalog was not confirmed');
      return;
    }
    setCatalog(result.response);
    catalogStatus.textContent = result.response.models.length
      ? 'API Live models loaded. Live uses this selection, available local tools and audio replies. Uncheck Live for REST chat.'
      : 'API returned no models with Live capability. No fallback list was added.';
  });
  window.addEventListener('taskvex-key-saved', () => {
    setCatalog({ models: [] });
    if (catalogStatus) catalogStatus.textContent = 'Key changed. Load the Live catalog again.';
  });

  const mSel = document.getElementById('mSel');
  if (mSel) {
    mSel.addEventListener('change', async function () {
      sfx.blip();
      const previous = store.conn?.model;
      const result = await emit('model', this.value);
      if (!result.ok) { if (previous) this.value = previous; return; }
      store.conn = store.conn || {};
      store.conn.model = this.value;
      window.dispatchEvent(new CustomEvent('taskvex-live-model-ready', {detail:{ready:true}}));
      if (isBackendAvailable() && catalogStatus) catalogStatus.textContent = 'Live model selected. REST text model is unchanged.';
      saveStoreCb?.();
    });
  }

  const vs = document.getElementById('vSel');
  if (vs) {
    vs.addEventListener('change', function () {
      sfx.blip();
      emit('voice', this.value);
    });
  }

  const gConnB = document.getElementById('gConnB');
  if (gConnB) {
    gConnB.addEventListener('click', async () => {
      if (gConnB.disabled) return;
      sfx.start();
      const statusEl = document.getElementById('gConnStatus');
      if (!isBackendAvailable()) {
        if (statusEl) statusEl.textContent = 'Connection unavailable (offline)';
        return;
      }
      gConnB.disabled = true;
      if (statusEl) statusEl.textContent = 'Awaiting authorization…';

      if (gConnTimer) clearTimeout(gConnTimer);
      gConnTimer = setTimeout(() => {
        gConnTimer = null;
        if (statusEl) statusEl.textContent = 'Authorization timed out';
        gConnB.disabled = false;
      }, 30000);

      try {
        const res = await emit('google_connect');
        if (!res || !res.ok) {
          if (gConnTimer) { clearTimeout(gConnTimer); gConnTimer = null; }
          gConnB.disabled = false;
          if (statusEl) statusEl.textContent = 'Authorization failed';
        }
      } catch {
        if (gConnTimer) { clearTimeout(gConnTimer); gConnTimer = null; }
        gConnB.disabled = false;
        if (statusEl) statusEl.textContent = 'Authorization failed';
      }
    });
  }

  const locSaveB = document.getElementById('locSaveB');
  if (locSaveB) {
    locSaveB.addEventListener('click', async () => {
      if (locOperation.pending) return;
      if (locOperation.uncertain) { await checkLocationStatus(); return; }
      sfx.blip();
      const locIn = document.getElementById('locIn');
      const locMsg = document.getElementById('locMsg');
      const val = (locIn && locIn.value.trim()) || '';
      if (!val) return;
      if (!isBackendAvailable()) {
        if (locMsg) locMsg.textContent = 'Failed to save location: Backend offline';
        return;
      }
      const curReqId = locOperation.begin();

      if (locMsg) locMsg.textContent = `Saving location: ${val} (awaiting confirmation)…`;
      const res = await emit('location', { name: val, auto: false });

      if (!locOperation.isCurrent(curReqId)) return;

      const resp = res?.response;

      if (!res || !res.ok) {
        locOperation.finish();
        const errMsg = sanitizeError(res?.error || resp?.error || 'Rejected by backend');
        if (locMsg) locMsg.textContent = `Failed to save location: ${errMsg}`;
        return;
      }

      // Check explicit negative field (general ok:true must not suppress saved:false)
      if (resp && typeof resp === 'object' && resp.saved === false) {
        locOperation.finish();
        const errMsg = sanitizeError(resp.error || 'Location not saved');
        if (locMsg) locMsg.textContent = `Failed to save location: ${errMsg}`;
        return;
      }

      // Explicit completion occurs when:
      // response.saved === true, OR
      // response.completed === true && response.saved !== false
      const isExplicitlyCompleted = (
        resp && typeof resp === 'object' && (
          resp.saved === true ||
          (resp.completed === true && resp.saved !== false)
        )
      );

      if (isExplicitlyCompleted) {
        locOperation.finish();
        locConfirmedValue = val;
        if (locMsg) locMsg.textContent = 'Manual location saved: ' + val;
        if (saveStoreCb) saveStoreCb();
      } else {
        // Request accepted / pending confirmation from backend bridge notification (e.g. window.vex.setLocation)
        if (locMsg) locMsg.textContent = `Location request accepted: ${val} (awaiting confirmation)…`;
      }
    });
  }

  const locAutoB = document.getElementById('locAutoB');
  if (locAutoB) {
    locAutoB.addEventListener('click', async () => {
      if (locOperation.pending) return;
      if (locOperation.uncertain) { await checkLocationStatus(); return; }
      sfx.blip();
      const locIn = document.getElementById('locIn');
      const locMsg = document.getElementById('locMsg');
      if (!isBackendAvailable()) {
        if (locMsg) locMsg.textContent = 'Auto location unavailable: Backend offline';
        return;
      }
      if (locIn) locIn.value = '';
      const curReqId = locOperation.begin();
      if (locMsg) locMsg.textContent = 'Detecting device location automatically…';
      const res = await emit('location', { auto: true });
      if (!locOperation.isCurrent(curReqId)) return;
      if (!res || !res.ok) {
        locOperation.finish();
        if (locMsg) locMsg.textContent = 'Failed to detect location';
      } else if (res.response && typeof res.response === 'object') {
        setLocationStatus(res.response, { emitSave: true });
      }
    });
  }

  // Media widget controls
  const mediaWidget = document.getElementById('w_media');
  if (mediaWidget) {
    mediaWidget.addEventListener('click', e => {
      const btn = e.target.closest('[data-m]');
      if (!btn) return;
      const action = btn.dataset.m;
      emit('media', action);
      sfx.media();

      const actionNames = {
        prev: 'Previous track',
        toggle: 'Play / pause',
        next: 'Next track'
      };
      if (addTimelineCb && actionNames[action]) {
        addTimelineCb(actionNames[action], null, 'media');
      }
    });
  }

const alertedCalendarEvents = new Set();

  // Calendar reminder alert scanner (every 30s)
  stopCalendarScheduler();
  calendarTimer = setInterval(() => {
    const d = new Date();
    const nowMin = d.getHours() * 60 + d.getMinutes();
    calEvents.forEach(ev => {
      if (!ev) return;
      const m = /^(\d{1,2}):(\d\d)/.exec(ev.t || '');
      const key = d.toDateString() + '+' + (ev.t || '') + '+' + (ev.s || '');
      if (!m || alertedCalendarEvents.has(key)) return;
      const diff = +m[1] * 60 + +m[2] - nowMin;
      if (diff >= 0 && diff <= 10) {
        alertedCalendarEvents.add(key);
        sfx.warn();
        if (logMessageCb) logMessageCb('Upcoming: ' + ev.t + ' ' + (ev.s || ''));
        const payload = { ...ev };
        delete payload._alerted;
        emit('cal_soon', payload);
      }
    });
  }, 30000);
}

let calendarTimer = null;
export function stopCalendarScheduler() {
  clearInterval(calendarTimer);
  calendarTimer = null;
}
window.addEventListener('pagehide', event => {
  if (!event.persisted) stopCalendarScheduler();
});
