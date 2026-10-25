/** Single UI adapter that manages device list and browser device IDs.
 * Does not initiate permission/registration; I/O resources remain with live_mic/live_audio/live_video.
 * Preference registration is delivered to the existing saveAll line of the form. */
import {store} from './preferences.js';
import {sfx} from './sfx.js';
import {emit, isBackendAvailable} from './api.js';
let savePreference = null;
export function initDeviceSettings(save) { savePreference = save; }
let devQueryTimer = null;
let deviceQueryPending = false, deviceQueryRevision = 0, nativeDevicesScanned = false;

/** Don't mix the browser device ID with the old Python hardware index.
 * Default is open selection; No silent fallback on disappearing/unselectable specific device.
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
      } else if (isBackendAvailable() && ['dIn', 'dOut', 'dCam'].includes(selId)) {
        // Keep a missing saved device visible; never silently select a replacement.
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
      if (isBackendAvailable() && ['dIn', 'dOut', 'dCam'].includes(selId)) {
        const message = document.getElementById('devMsg');
        const saved = savePreference?.({emitSave:false});
        if (message) message.textContent = saved
          ? 'Selection cached; applies to the next capture / Live reply. Save Settings to persist in desktop storage.'
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
    if (message) message.textContent = 'Refreshing audio and camera devices…';
    try {
      // Listing never requests capture permission; only Mic/Camera On can request it.
      // after permission, the same function lists device names and devices again.
      const devices = await navigator.mediaDevices.enumerateDevices();
      if (revision !== deviceQueryRevision) return;
      const list = kind => [{deviceId:'default', name:'System default'}, ...devices
        .filter(d => d.kind === kind && d.deviceId && d.deviceId !== 'default')
        .map((d, i) => ({deviceId:d.deviceId, name:d.label || `${kind === 'videoinput' ? 'Camera' : 'Audio device'} ${i + 1}`}))];
      setDevices({inputs:list('audioinput'), outputs:list('audiooutput'), cameras:list('videoinput')});
      nativeDevicesScanned = true;
      if (message) message.textContent = 'Audio and camera devices listed automatically. If names are hidden, enable the relevant Microphone or Camera once to grant permission. Camera capture never starts automatically.';
    } catch {
      if (revision === deviceQueryRevision && message)
        message.textContent = 'Audio/camera devices unavailable or permission denied. Existing preferences were kept.';
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
      if (devMsg) devMsg.textContent = "No backend, devices could not be scanned";
      return;
    }
    devQueryTimer = setTimeout(() => {
      devQueryTimer = null;
      if (devMsg) devMsg.textContent = 'No device list was received';
    }, 10000);
  } catch {
    if (devMsg) devMsg.textContent = "No backend, devices could not be scanned";
  }
}

if (typeof window !== 'undefined') window.addEventListener('pagehide', () => { deviceQueryRevision++; });
if (typeof navigator !== 'undefined') navigator.mediaDevices?.addEventListener?.('devicechange', () => {
  if (nativeDevicesScanned) queryDevices();
});

