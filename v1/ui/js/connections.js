/**
 * connections.js - Canlı model kataloğu ve salt okunur widget görünümleri.
 */

import { sfx } from './sfx.js';
import { emit, isBackendAvailable, sanitizeError, createPendingOperation } from './api.js';
import { store, saveSettingsConfirmed } from './settings.js';

let isPlayingMedia = false;
let calEvents = [];
let warnedHighApi = false;
let saveStoreCb = null;
// Native hazır ve anahtar değişimi aynı tek katalog işlemini kullanır.
const catalogOperation = createPendingOperation(() => {
  const status = document.getElementById('liveCatalogStatus');
  if (status) status.textContent = 'Catalog result unknown. Reopen the app before loading again.';
}, 65000);
export async function loadLiveModels() {
  if (!isBackendAvailable() || catalogOperation.pending || catalogOperation.uncertain) return false;
  const status = document.getElementById('liveCatalogStatus');
  const revision = catalogOperation.begin();
  setCatalog({models:[]});
  if (status) status.textContent = 'Loading Live models from Gemini API…';
  const result = await emit('query_catalog');
  if (!catalogOperation.isCurrent(revision)) return false;
  catalogOperation.finish();
  if (!result.ok || result.response?.completed !== true || !Array.isArray(result.response.models)) {
    if (status) status.textContent = sanitizeError(result.error || result.response?.error || 'Catalog was not confirmed') + ' Reopen the app or save your key to try again.';
    return false;
  }
  setCatalog(result.response);
  if (status) status.textContent = result.response.models.length
    ? 'API Live models loaded automatically. Saved Live selection restored when available.'
    : 'API returned no conversational Live models.';
  if (result.response.models.length) saveStoreCb?.();
  return true;
}

export function setCatalog(cat) {
  if (!cat) return;

  const vs = document.getElementById('vSel');
  if (vs && Array.isArray(cat.voices)) {
    const voices = cat.voices.filter(v => v?.live === true && typeof v.id === 'string' && v.id);
    vs.innerHTML = '';
    for (const voice of voices) {
      const option = document.createElement('option');
      option.value = voice.id;
      option.textContent = '[LIVE] ' + voice.name;
      vs.append(option);
    }
    vs.disabled = !voices.length;
    if (voices.length) {
      vs.value = voices.some(v => v.id === store.conn?.voice) ? store.conn.voice
        : voices.some(v => v.id === 'Puck') ? 'Puck' : voices[0].id;
      store.conn = store.conn || {};
      store.conn.voice = vs.value;
    } else vs.append(new Option('Live voices unavailable', '', true, true));
  }

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

}

export function setGoogleStatus(st) {
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
  document.getElementById('vSel')?.addEventListener('change', async () => {
    sfx.blip();
    const status = document.getElementById('voiceStatus');
    const saved = await saveSettingsConfirmed();
    if (status) status.textContent = saved
      ? 'Live voice saved. Applies to the next Live reply; the current reply continues.'
      : 'Voice save was not confirmed. Check settings before the next reply.';
  });

  // Native başlangıcı ve anahtar kaydı API kataloğunu otomatik yükler. Boş/hatalı katalog
  // sabit model adlarıyla doldurulmaz; katalog başarısı Live bağlantısı değildir.
  const catalogStatus = document.getElementById('liveCatalogStatus');
  window.addEventListener('taskvex-key-saved', () => { void loadLiveModels(); });

  const mSel = document.getElementById('mSel');
  if (mSel) {
    mSel.addEventListener('change', async function () {
      sfx.blip();
      const previous = store.conn?.model;
      const result = await emit('model', this.value);
      if (!result.ok || result.response?.completed !== true || result.response?.model !== this.value) { if (previous) this.value = previous; return; }
      store.conn = store.conn || {};
      store.conn.model = this.value;
      window.dispatchEvent(new CustomEvent('taskvex-live-model-ready', {detail:{ready:true}}));
      if (isBackendAvailable() && catalogStatus) catalogStatus.textContent = 'Live model selected. REST text model is unchanged.';
      saveStoreCb?.();
    });
  }

}
