/** Shared data contracts. No DOM, storage or backend side effects. */
export function foldTr(s) {
  return String(s || '')
    .toLocaleLowerCase('tr')
    .replace(/ı/g, 'i')
    .replace(/ğ/g, 'g')
    .replace(/ü/g, 'u')
    .replace(/ş/g, 's')
    .replace(/ö/g, 'o')
    .replace(/ç/g, 'c');
}

let idSequence = 0;
export function uniqueRecordId(records, prefix) {
  const used = new Set(records.map(r => r?.id).filter(id => typeof id === 'string' || Number.isFinite(id)).map(String));
  let id;
  do { id = prefix + '_' + (globalThis.crypto?.randomUUID?.() || `${Date.now()}_${++idSequence}`); }
  while (used.has(id));
  return id;
}

const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const text = value => typeof value === 'string';
const numeric = value => typeof value === 'number' && Number.isFinite(value);
const numOrNumStr = value => numeric(value) || (text(value) && !isNaN(Number(value)) && value.trim() !== '');
const optional = (value, check) => value == null || check(value);

/** Oluşturulma zamanı: eksik/null bilinmiyor demektir; tarih uydurulmaz. */
export function validNoteCreatedAt(value) {
  if (value == null) return true;
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value)) return false;
  const date = new Date(value);
  return Number.isFinite(date.getTime()) && date.getUTCFullYear() >= 1 && date.toISOString() === value;
}

function logToUI(msg) {
  console.warn(msg);
  if (typeof document !== 'undefined') {
    const logEl = document.getElementById('log');
    if (logEl) {
      const d = document.createElement('div');
      d.className = 'l4';
      d.textContent = '› ' + msg;
      logEl.prepend(d);
    }
  }
}

export function normalizeTimeline(items) {
  if (!Array.isArray(items)) return { ok: false, error: 'Timeline must be an array' };
  const value = [];
  for (const item of items) {
    if (!record(item) || !text(item.x) || !optional(item.k, text) || !optional(item.ok, v => typeof v === 'boolean') || !(numeric(item.t) || text(item.t)) || !Number.isFinite(new Date(item.t).getTime())) {
      return { ok: false, error: 'Invalid timeline record' };
    }
    value.push({ t: item.t, x: item.x, ok: item.ok ?? null, k: item.k || '' });
  }
  return { ok: true, value: value.slice(-300) };
}

function validateAdditionalFields(candidate) {
  for (const key of ['calendar', 'reminders']) {
    if (candidate[key] == null) continue;
    if (!Array.isArray(candidate[key])) {
      logToUI(`Skipped invalid ${key}: must be an array or null`);
      delete candidate[key];
      continue;
    }
    const valid = [];
    for (const item of candidate[key]) {
      if (key === 'reminders' && text(item)) { valid.push(item); continue; }
      if (!record(item) || !optional(item.t, text) || !optional(item.s, text)) {
        logToUI(`Skipped invalid ${key} record`);
        continue;
      }
      valid.push(item);
    }
    candidate[key] = valid;
  }
  if (candidate.timeline !== undefined) {
    if (candidate.timeline === null) {
      candidate.timeline = [];
    } else if (!Array.isArray(candidate.timeline)) {
      logToUI('Skipped invalid timeline: must be an array or null');
      delete candidate.timeline;
    } else {
      const normalized = normalizeTimeline(candidate.timeline);
      if (!normalized.ok) {
        logToUI(`Skipped invalid timeline items: ${normalized.error}`);
        const valid = [];
        for (const item of candidate.timeline) {
          if (record(item) && text(item.x) && optional(item.k, text) && optional(item.ok, v => typeof v === 'boolean') && (numeric(item.t) || text(item.t)) && Number.isFinite(new Date(item.t).getTime())) {
            valid.push({ t: item.t, x: item.x, ok: item.ok ?? null, k: item.k || '' });
          }
        }
        candidate.timeline = valid.slice(-300);
      } else {
        candidate.timeline = normalized.value;
      }
    }
  }
  const fields = {
    weather: { temp: numOrNumStr, feels: numOrNumStr, hum: numOrNumStr, wind: numOrNumStr, place: text, desc: text },
    telemetry: { cpu: numeric, gpu: numeric, ram: numeric, cpuT: numeric, gpuT: numeric, ramTxt: text, bat: v => text(v) || numeric(v), disk: v => text(v) || numeric(v), win: text },
    network: { ping: numeric, down: numeric, wifi: numeric, api: numeric },
    media: { title: text, artist: text, playing: v => typeof v === 'boolean' },
    googleStatus: { connected: v => typeof v === 'boolean', email: text, error: text }
  };
  for (const [key, checks] of Object.entries(fields)) {
    if (candidate[key] == null) continue;
    if (!record(candidate[key])) {
      logToUI(`Skipped invalid ${key}: must be an object or null`);
      delete candidate[key];
      continue;
    }
    for (const [field, check] of Object.entries(checks)) {
      const val = candidate[key][field];
      if (val !== undefined && val !== null) {
        if (!check(val)) {
          logToUI(`Skipped invalid field ${key}.${field}`);
          delete candidate[key][field];
        } else if (key === 'weather' && typeof val === 'string' && ['temp', 'feels', 'hum', 'wind'].includes(field)) {
          candidate[key][field] = Number(val);
        }
      }
    }
  }
  if (candidate.tokens != null) {
    const t = candidate.tokens;
    if (!Array.isArray(t) && !record(t)) {
      logToUI('Skipped invalid tokens: must be array or object');
      delete candidate.tokens;
    } else {
      const values = Array.isArray(t) ? t : [t.used, t.max, t.isEst];
      if (!optional(values[0], numeric) || !optional(values[1], numeric) || !optional(values[2], v => typeof v === 'boolean')) {
        logToUI('Skipped invalid token values');
        delete candidate.tokens;
      }
    }
  }
  if (candidate.devices != null) {
    if (!record(candidate.devices)) {
      logToUI('Skipped invalid devices: must be an object');
      delete candidate.devices;
    } else {
      for (const key of ['inputs', 'outputs', 'cameras']) {
        const list = candidate.devices[key];
        if (list == null) continue;
        if (!Array.isArray(list)) {
          logToUI(`Skipped invalid devices.${key}: must be an array`);
          delete candidate.devices[key];
          continue;
        }
        const valid = [];
        for (const d of list) {
          if (!record(d) || !optional(d.name, text) || !optional(d.label, text) || !optional(d.deviceId, text)) {
            logToUI(`Skipped invalid device record in devices.${key}`);
            continue;
          }
          if (d.index != null && !(Number.isSafeInteger(d.index) || (text(d.index) && /^-?\d+$/.test(d.index) && Number.isSafeInteger(Number(d.index))))) {
            logToUI(`Skipped invalid device index in devices.${key}`);
            continue;
          }
          valid.push(d);
        }
        candidate.devices[key] = valid;
      }
      for (const key of ['currentIn', 'currentOut', 'currentCam']) {
        if (!optional(candidate.devices[key], v => text(v) || numeric(v))) {
          logToUI(`Skipped invalid current device ${key}`);
          delete candidate.devices[key];
        }
      }
    }
  }
  if (candidate.catalog != null) {
    if (!record(candidate.catalog)) {
      logToUI('Skipped invalid catalog: must be an object');
      delete candidate.catalog;
    } else {
      for (const key of ['models', 'voices']) {
        const list = candidate.catalog[key];
        if (list === undefined) continue;
        if (!Array.isArray(list)) {
          logToUI(`Skipped invalid catalog.${key}: must be an array`);
          delete candidate.catalog[key];
          continue;
        }
        const valid = [];
        for (const item of list) {
          if (!record(item) || !text(item.id) || !text(item.name) || !optional(item.desc, text) || !optional(item.persona, text) || !optional(item.gender, text)) {
            logToUI(`Skipped invalid catalog record in catalog.${key}`);
            continue;
          }
          valid.push(item);
        }
        candidate.catalog[key] = valid;
      }
    }
  }
  for (const key of ['colors', 'devs', 'prof', 'conn']) {
    if (candidate[key] === null) candidate[key] = {};
    if (candidate[key] === undefined) continue;
    if (!record(candidate[key])) {
      logToUI(`Skipped invalid ${key}: must be an object`);
      candidate[key] = {};
      continue;
    }
    for (const [k, value] of Object.entries(candidate[key])) {
      if (value !== null && !['string', 'number', 'boolean'].includes(typeof value)) {
        logToUI(`Skipped invalid ${key}.${k}`);
        delete candidate[key][k];
      }
    }
  }
  for (const key of ['sfx', 'onTop']) {
    if (!optional(candidate[key], v => typeof v === 'boolean')) {
      logToUI(`Skipped invalid ${key}`);
      delete candidate[key];
    }
  }
  if (candidate.prof) {
    for (const [key, value] of Object.entries(candidate.prof)) {
      if (!optional(value, ['pTab', 'pApp'].includes(key) ? v => typeof v === 'boolean' : text)) {
        logToUI(`Skipped invalid profile field ${key}`);
        delete candidate.prof[key];
      }
    }
  }
  for (const key of ['vol', 'wake', 'noise']) {
    if (!optional(candidate[key], numeric)) {
      logToUI(`Skipped invalid ${key}`);
      delete candidate[key];
    }
  }
  for (const key of ['cmp', 'tab']) {
    if (!optional(candidate[key], text)) {
      logToUI(`Skipped invalid ${key}`);
      delete candidate[key];
    }
  }
  return null;
}

export function validateSkillSteps(steps) {
  if (!Array.isArray(steps)) return 'Steps must be a JSON array of step objects.';
  const types = new Set(['open_app', 'interact_element', 'hotkey', 'type_text', 'wait']);
  for (const [i, step] of steps.entries()) {
    if (!step || typeof step !== 'object' || Array.isArray(step)) return 'Step ' + (i + 1) + ' must be an object.';
    if (!types.has(step.step_type)) {
      logToUI('Warning: Step ' + (i + 1) + ' has unknown step_type: ' + step.step_type);
    }
    for (const field of ['target', 'text', 'action', 'app_name']) {
      if (step[field] !== undefined && typeof step[field] !== 'string') return 'Step ' + (i + 1) + ': ' + field + ' must be text.';
    }
    if (step.wait_after !== undefined && (typeof step.wait_after !== 'number' || !Number.isFinite(step.wait_after) || step.wait_after < 0)) return 'Step ' + (i + 1) + ': wait_after must be a nonnegative number.';
    if (step.press_enter !== undefined && typeof step.press_enter !== 'boolean') return 'Step ' + (i + 1) + ': press_enter must be boolean.';
  }
  return null;
}

export function normalizeRoutineSteps(steps) {
  return typeof steps === 'string' ? steps : Array.isArray(steps) ? steps.filter(s => typeof s === 'string').join('\n') : '';
}

export function validateAndNormalizeSnapshot(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return { ok: false, error: 'Snapshot must be a non-null object' };
  }

  const candidate = {};

  // 1. Notes validation & normalization
  if (data.notes !== undefined) {
    if (data.notes === null) {
      candidate.notes = null;
    } else if (Array.isArray(data.notes)) {
      const normalizedNotes = [];
      const noteIds = new Set();
      for (const item of data.notes) {
        if (item && typeof item === 'object' && !validNoteCreatedAt(item.created_at))
          return { ok: false, error: 'Invalid note creation time' };
        if (typeof item === 'string') {
          normalizedNotes.push({ t: item, d: 0 });
        } else if (item && typeof item === 'object' && !Array.isArray(item)) {
          if (item.id !== undefined) {
            if (typeof item.id !== 'string' || !item.id.trim() || noteIds.has(item.id)) {
              logToUI('Skipped note with invalid or duplicate id');
              continue;
            }
            noteIds.add(item.id);
          }
          if (item.t !== undefined && typeof item.t !== 'string' && typeof item.t !== 'number') {
            logToUI('Skipped note with invalid text');
            continue;
          }
          normalizedNotes.push({
            ...(item.id !== undefined ? { id: item.id } : {}),
            ...(item.created_at !== undefined ? { created_at: item.created_at } : {}),
            t: item.t != null ? String(item.t) : '',
            d: item.d ? 1 : 0
          });
        } else {
          logToUI('Skipped invalid note element');
          continue;
        }
      }
      candidate.notes = normalizedNotes;
    } else {
      logToUI('Skipped invalid notes: must be an array or null');
    }
  }

  // 2. Skills validation & normalization
  if (data.skills !== undefined) {
    if (data.skills === null) {
      candidate.skills = null;
    } else if (Array.isArray(data.skills)) {
      const normalizedSkills = [];
      const seenIds = new Set();
      for (const s of data.skills) {
        if (!s || typeof s !== 'object' || Array.isArray(s)) {
          logToUI('Skipped invalid skill: must be an object');
          continue;
        }
        if (s.id != null && !(text(s.id) || numeric(s.id))) {
          logToUI('Skipped skill with invalid id');
          continue;
        }
        if (text(s.id) && !s.id.trim()) {
          logToUI('Skipped skill with empty id');
          continue;
        }
        if (s.name !== undefined && typeof s.name !== 'string') {
          logToUI('Skipped skill with invalid name');
          continue;
        }
        let invalid = false;
        for (const key of ['trigger', 'app_name', 'desc', 'description', 'skill_name']) {
          if (!optional(s[key], text)) { invalid = true; break; }
        }
        if (invalid) {
          logToUI(`Skipped skill with invalid text properties: ${s.id || 'unnamed'}`);
          continue;
        }
        for (const key of ['last', 'runs', 'ok']) {
          if (!optional(s[key], v => text(v) || numeric(v))) { invalid = true; break; }
        }
        if (invalid) {
          logToUI(`Skipped skill with invalid stat fields: ${s.id || 'unnamed'}`);
          continue;
        }
        for (const key of ['params', 'parameters']) {
          if (!optional(s[key], v => text(v) || (Array.isArray(v) && v.every(text)))) { invalid = true; break; }
        }
        if (invalid) {
          logToUI(`Skipped skill with invalid params: ${s.id || 'unnamed'}`);
          continue;
        }
        if (s.steps !== undefined && s.steps !== null && !Array.isArray(s.steps) && typeof s.steps !== 'string') {
          logToUI(`Skipped skill with invalid steps: ${s.id || 'unnamed'}`);
          continue;
        }
        let steps = s.steps == null ? [] : s.steps;
        if (typeof steps === 'string') {
          try { steps = JSON.parse(steps); } catch {
            logToUI(`Skipped skill with invalid steps JSON: ${s.id || 'unnamed'}`);
            continue;
          }
        }
        const stepsError = validateSkillSteps(steps);
        if (stepsError) {
          logToUI(`Skipped skill: ${stepsError}`);
          continue;
        }
        const id = s.id != null ? String(s.id) : uniqueRecordId([...data.skills, ...normalizedSkills], 'sk');
        if (seenIds.has(id)) {
          logToUI(`Skipped duplicate skill id: ${id}`);
          continue;
        }
        seenIds.add(id);
        normalizedSkills.push({
          ...s,
          id,
          name: s.name != null ? String(s.name) : 'Unnamed skill',
          desc: s.desc != null ? String(s.desc) : (s.description != null ? String(s.description) : ''),
          steps
        });
      }
      candidate.skills = normalizedSkills;
    } else {
      logToUI('Skipped invalid skills: must be an array or null');
    }
  }

  // 3. Routines validation & normalization
  if (data.routines !== undefined) {
    if (data.routines === null) {
      candidate.routines = null;
    } else if (Array.isArray(data.routines)) {
      const normalizedRoutines = [];
      const seenIds = new Set();
      for (const r of data.routines) {
        if (!r || typeof r !== 'object' || Array.isArray(r)) {
          logToUI('Skipped invalid routine: must be an object');
          continue;
        }
        if (r.id != null && !(text(r.id) || numeric(r.id))) {
          logToUI('Skipped routine with invalid id');
          continue;
        }
        if (text(r.id) && !r.id.trim()) {
          logToUI('Skipped routine with empty id');
          continue;
        }
        if (r.name !== undefined && typeof r.name !== 'string') {
          logToUI('Skipped routine with invalid name');
          continue;
        }
        let invalid = false;
        for (const key of ['val', 'last']) {
          if (!optional(r[key], v => text(v) || numeric(v))) { invalid = true; break; }
        }
        if (invalid) {
          logToUI(`Skipped routine with invalid val/last: ${r.id || 'unnamed'}`);
          continue;
        }
        let steps = '';
        if (typeof r.steps === 'string') {
          steps = r.steps;
        } else if (Array.isArray(r.steps)) {
          logToUI(`Routine ${r.id || 'unnamed'} steps array converted to string`);
          steps = normalizeRoutineSteps(r.steps);
        } else if (r.steps != null) {
          logToUI(`Skipped routine with invalid steps: ${r.id || 'unnamed'}`);
          continue;
        }
        const id = r.id != null ? String(r.id) : uniqueRecordId([...data.routines, ...normalizedRoutines], 'rt');
        if (seenIds.has(id)) {
          logToUI(`Skipped duplicate routine id: ${id}`);
          continue;
        }
        seenIds.add(id);
        normalizedRoutines.push({
          ...r,
          id,
          name: r.name != null ? String(r.name) : 'Unnamed routine',
          type: typeof r.type === 'string' ? r.type : 'manual',
          val: r.val != null ? String(r.val) : '',
          days: typeof r.days === 'string' ? r.days : 'all',
          steps,
          on: r.on ? 1 : 0
        });
      }
      candidate.routines = normalizedRoutines;
    } else {
      logToUI('Skipped invalid routines: must be an array or null');
    }
  }

  // 4. Layout validation & normalization
  if (data.layout !== undefined) {
    if (data.layout === null) {
      candidate.layout = null;
    } else if (Array.isArray(data.layout)) {
      candidate.layout = sanitizeLayout(data.layout);
    } else {
      logToUI('Skipped invalid layout: must be an array or null');
    }
  }

  // 5. Settings fields
  if (data.theme !== undefined) {
    if (data.theme !== null && typeof data.theme !== 'string') {
      logToUI('Skipped invalid theme: must be a string or null');
    } else {
      candidate.theme = data.theme;
    }
  }
  for (const key of ['colors', 'devs', 'prof', 'conn']) {
    if (data[key] !== undefined) {
      if (data[key] !== null && (typeof data[key] !== 'object' || Array.isArray(data[key]))) {
        logToUI(`Skipped invalid ${key}: must be an object or null`);
      } else {
        candidate[key] = data[key];
      }
    }
  }

  // Optional pass-throughs
  [
    'sfx', 'vol', 'wake', 'noise', 'onTop', 'cmp', 'tab',
    'calendar', 'reminders', 'weather', 'telemetry', 'tokens',
    'network', 'media', 'googleStatus', 'timeline', 'devices', 'catalog'
  ].forEach(k => {
    if (data[k] !== undefined) candidate[k] = data[k];
  });

  validateAdditionalFields(candidate);
  return { ok: true, candidate };
}

export function validateSnapshot(data) {
  return validateAndNormalizeSnapshot(data);
}

export const ALLOWED_WIDGET_IDS = new Set([
  'time',
  'system',
  'timer',
  'weather',
  'calendar',
  'remind',
  'notes',
  'media',
  'net',
  'log'
]);

export const LD = [
  ['time', 'L'],
  ['system', 'L'],
  ['timer', 'L'],
  ['weather', 'R'],
  ['calendar', 'R'],
  ['remind', 'R'],
  ['notes', 'R'],
  ['media', 'R'],
  ['net', 'R'],
  ['log', 'R']
].map(a => ({ id: a[0], c: a[1], on: 1, sz: 1 }));

export function sanitizeLayout(candidate) {
  if (!Array.isArray(candidate)) return JSON.parse(JSON.stringify(LD));
  const seen = new Set();
  const valid = [];
  for (const w of candidate) {
    if (!w || typeof w !== 'object') continue;
    if (!ALLOWED_WIDGET_IDS.has(w.id)) continue;
    if (seen.has(w.id)) continue;
    seen.add(w.id);
    valid.push({
      id: w.id,
      c: w.c === 'L' ? 'L' : 'R',
      on: w.on ? 1 : 0,
      sz: typeof w.sz === 'number' && w.sz >= 0 && w.sz < 3 ? w.sz : 1
    });
  }
  for (const item of LD) {
    if (!seen.has(item.id)) {
      valid.push({ id: item.id, c: item.c, on: item.on, sz: item.sz });
    }
  }
  return valid;
}
