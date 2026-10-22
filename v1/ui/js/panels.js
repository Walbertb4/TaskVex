/**
 * panels.js - Modals, drawer, command palette, and action timeline
 */

import { sfx } from './sfx.js';
import { emit, logBridgeError } from './api.js';
import { writeStoredJSON } from './storage.js';
import { S } from './reactor.js';
import { normalizeTimeline, foldTr } from './schema.js';

const DEBUG = false;

let TL = [];
let palSel = 0;
let palItems = [];
let queryDevicesCb = null;
let renderRoutinesCb = null;
let getSkillsCb = () => [];
let getRoutinesCb = () => [];
let runSkillCb = () => {};
let runRoutineCb = () => {};
let addNoteCb = () => {};
let sendTextCb = () => {};
let setStateCb = () => {};
let getProfileShortcutsCb = () => '';

const pad2 = n => String(n).padStart(2, '0');
let modalReturnFocus = null;
const inertBeforeModal = new Map();

function modalControls(modal) {
  return [...modal.querySelectorAll('button,input,select,textarea,a[href],[tabindex]')]
    .filter(el => !el.disabled && el.tabIndex >= 0 && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
}

function tlLoad() {
  try {
    TL = JSON.parse(localStorage.getItem('taskvex_tl') || localStorage.getItem('jarvis_tl') || '[]');
  } catch (error) {
    TL = [];
    logBridgeError('timeline read', error);
  }
  const normalized = normalizeTimeline(TL);
  if (normalized.ok) TL = normalized.value;
  else {
    TL = Array.isArray(TL) ? TL.flatMap(item => { const r = normalizeTimeline([item]); return r.ok ? r.value : []; }) : [];
    logBridgeError('timeline recovery', new Error(normalized.error));
  }
}

function tlSave() {
  return writeStoredJSON('taskvex_tl', TL.slice(-300));
}

export function addTL(x, ok = null, k = '', silent = false) {
  const e = {
    t: Date.now(),
    x: String(x),
    ok: ok == null ? null : !!ok,
    k: k || ''
  };
  TL.push(e);
  if (TL.length > 300) TL.shift();
  tlSave();

  const mTl = document.getElementById('mTl');
  if (mTl && mTl.classList.contains('o')) {
    renderTL();
  }

  if (!silent) emit('timeline', e);
}

export function setTimeline(a) {
  const result = normalizeTimeline(a ?? []);
  if (!result.ok) { logBridgeError('timeline update', new Error(result.error)); return false; }
  TL = result.value;
  tlSave();
  renderTL();
  return true;
}

export function renderTL() {
  const tlQ = document.getElementById('tlQ');
  const tlF = document.getElementById('tlF');
  const container = document.getElementById('tlList');
  if (!container) return;

  const q = foldTr((tlQ && tlQ.value) || '');
  const fl = (tlF && tlF.value) || '';

  container.innerHTML = '';
  const filtered = TL.slice().reverse().filter(e => {
    const matchQ = !q || foldTr(e.x).includes(q);
    const matchF = !fl || (fl === 'bad' ? e.ok === false : e.ok === true);
    return matchQ && matchF;
  });

  if (!filtered.length) {
    const empty = document.createElement('div');
    empty.className = 'sub';
    empty.style.textTransform = 'none';
    empty.textContent = 'No records.';
    container.append(empty);
    return;
  }

  let currentDay = '';
  filtered.forEach(e => {
    const d = new Date(e.t);
    const dayStr = d.toLocaleDateString('en-US', { day: 'numeric', month: 'long' });
    if (dayStr !== currentDay) {
      currentDay = dayStr;
      const dayHeader = document.createElement('div');
      dayHeader.className = 'tld';
      dayHeader.textContent = dayStr;
      container.append(dayHeader);
    }

    const row = document.createElement('div');
    row.className = 'tl' + (e.ok === false ? ' bad' : e.ok ? ' ok' : '');

    const timeEl = document.createElement('time');
    timeEl.textContent = `${pad2(d.getHours())}:${pad2(d.getMinutes())}`;

    const icon = document.createElement('i');
    icon.textContent = e.ok === false ? '✗' : e.ok ? '✓' : '›';

    const textSpan = document.createElement('span');
    textSpan.textContent = e.x;

    row.append(timeEl, icon, textSpan);
    container.append(row);
  });
}

export function showM(id) {
  const target = document.getElementById(id);
  if (!target || target.classList.contains('o')) return;
  openM(id);
}

export function openM(id) {
  const target = document.getElementById(id);
  if (!target) return;

  if (target.classList.contains('o')) {
    closeM();
    return;
  }

  const alreadyOpen = document.querySelector('.modal.o');
  if (!alreadyOpen) modalReturnFocus = document.activeElement;
  for (const [el, inert] of inertBeforeModal) el.inert = inert;
  inertBeforeModal.clear();

  document.querySelectorAll('.modal.o').forEach(m => m.classList.remove('o'));
  target.classList.add('o');
  target.setAttribute('role', 'dialog');
  target.setAttribute('aria-modal', 'true');
  target.setAttribute('aria-label', target.querySelector('.h2 span')?.textContent || (id === 'mPal' ? 'Command palette' : id));
  target.tabIndex = -1;
  for (const el of document.body.children) {
    if (el === target || ['SCRIPT', 'STYLE', 'LINK'].includes(el.tagName)) continue;
    inertBeforeModal.set(el, el.inert);
    el.inert = true;
  }
  sfx.open();

  if (id === 'mSet' && queryDevicesCb) queryDevicesCb();
  if (id === 'mTl') renderTL();
  if (id === 'mRut' && renderRoutinesCb) renderRoutinesCb();
  (modalControls(target)[0] || target).focus({ preventScroll: true });
  // Visibility transitions can prevent focus in the opening event itself.
  requestAnimationFrame(function focusWhenVisible() {
    if (!target.classList.contains('o')) return;
    if (getComputedStyle(target).visibility === 'hidden') {
      requestAnimationFrame(focusWhenVisible);
      return;
    }
    if (!target.contains(document.activeElement)) (modalControls(target)[0] || target).focus({ preventScroll: true });
  });
}

export function closeM() {
  const openModals = document.querySelectorAll('.modal.o');
  if (openModals.length > 0) {
    openModals.forEach(m => m.classList.remove('o'));
    for (const [el, inert] of inertBeforeModal) el.inert = inert;
    inertBeforeModal.clear();
    if (modalReturnFocus?.isConnected && !modalReturnFocus.inert) modalReturnFocus.focus({ preventScroll: true });
    modalReturnFocus = null;
    sfx.close();
  }
}

export function toggleD() {
  const drawer = document.getElementById('drawer');
  if (!drawer) return;
  drawer.classList.toggle('o');
  const isOpen = drawer.classList.contains('o');
  if (isOpen) sfx.open();
  else sfx.close();
  emit('drawer', isOpen);
}

export function setScreen(d) {
  const scr = document.getElementById('scr');
  if (!scr) return;
  if (!d) {
    scr.style.background = '';
    scr.textContent = 'Live screen preview';
    return;
  }
  scr.textContent = '';
  scr.style.background = `url(${/^data:/.test(d) ? d : 'data:image/jpeg;base64,' + d}) center/contain no-repeat #000`;
}

function buildPaletteItems(query) {
  const q = foldTr(query);
  const palIn = document.getElementById('palIn');
  const raw = (palIn && palIn.value.trim()) || '';

  let it = [
    ['Settings', 'SETTING', () => openM('mSet')],
    ['Personalization', 'SETTING', () => openM('mProf')],
    ['Skill library', 'SETTING', () => openM('mSkill')],
    ['Widget layout', 'SETTING', () => openM('mLay')],
    ['Live screen', 'SETTING', toggleD],
    ['Compact view: on/off', 'VIEW', () => {
      const cmpSel = document.getElementById('cmpSel');
      if (cmpSel) {
        cmpSel.value = document.body.classList.contains('compact') ? 'off' : 'on';
        cmpSel.dispatchEvent(new Event('change'));
      }
    }],
    ['Action timeline', 'SETTING', () => openM('mTl')],
    ['Routines', 'SETTING', () => openM('mRut')],
    ['Shut down V.EX.', 'SYSTEM', () => {
      const shut = document.getElementById('shut');
      if (shut) shut.click();
    }]
  ];

  if (DEBUG) {
    Object.keys(S).forEach(k => {
      it.push(['State: ' + S[k][0], 'TEST', () => setStateCb(k)]);
    });
  }

  const skillsList = getSkillsCb();
  skillsList.forEach(s => {
    it.push([s.name, 'SKILL', () => runSkillCb(s)]);
  });

  const routinesList = getRoutinesCb();
  routinesList.forEach(r => {
    it.push([r.name, 'ROUTINE', () => runRoutineCb(r, 'palette')]);
  });

  const shortcutsRaw = getProfileShortcutsCb() || '';
  shortcutsRaw
    .split('\n')
    .map(l => {
      const idx = l.indexOf('=');
      if (idx === -1) return null;
      return [l.slice(0, idx).trim(), l.slice(idx + 1).trim()];
    })
    .filter(a => a && a[0])
    .forEach(([key, target]) => {
      it.push([
        `${key} → ${target}`,
        'SHORTCUT',
        () => {
          emit('shortcut', { key, target });
          addTL(`Shortcut: ${key} → ${target}`, null, 'shortcut');
        }
      ]);
    });

  it = it.filter(x => foldTr(x[0]).includes(q));

  if (raw) {
    it.push(['Send to V.EX.: ' + raw, 'MESSAGE', () => sendTextCb(raw)]);
    it.push(['Add note: ' + raw, 'NOTE', () => addNoteCb(raw)]);
  }

  return it;
}

function renderPalette() {
  const palIn = document.getElementById('palIn');
  const palList = document.getElementById('palList');
  if (!palIn || !palList) return;

  palItems = buildPaletteItems(palIn.value);
  palSel = Math.min(palSel, Math.max(0, palItems.length - 1));

  palList.innerHTML = '';
  if (!palItems.length) {
    const empty = document.createElement('div');
    empty.className = 'pi';
    empty.textContent = 'No results';
    palList.append(empty);
    return;
  }

  palItems.forEach((x, i) => {
    const item = document.createElement('div');
    item.className = 'pi' + (i === palSel ? ' a' : '');
    item.dataset.i = String(i);

    const titleSpan = document.createElement('span');
    titleSpan.textContent = x[0];

    const tagEm = document.createElement('em');
    tagEm.textContent = x[1];

    item.append(titleSpan, tagEm);
    palList.append(item);
  });
}

function runPaletteItem(i) {
  const x = palItems[i];
  if (!x) return;
  closeM();
  sfx.ok();
  x[2]();
}

export function initPanels(options = {}) {
  tlLoad();
  queryDevicesCb = options.queryDevices || null;
  renderRoutinesCb = options.renderRoutines || null;
  getSkillsCb = options.getSkills || (() => []);
  getRoutinesCb = options.getRoutines || (() => []);
  runSkillCb = options.runSkill || (() => {});
  runRoutineCb = options.runRoutine || (() => {});
  addNoteCb = options.addNote || (() => {});
  sendTextCb = options.sendText || (() => {});
  setStateCb = options.setState || (() => {});
  getProfileShortcutsCb = options.getProfileShortcuts || (() => '');

  // Close buttons inside modals
  document.querySelectorAll('.btnCloseM').forEach(b => {
    b.addEventListener('click', closeM);
  });

  const btnCloseDrawer = document.getElementById('btnCloseDrawer');
  if (btnCloseDrawer) btnCloseDrawer.addEventListener('click', toggleD);

  const scrT = document.getElementById('scrT');
  if (scrT) {
    scrT.addEventListener('change', function () {
      emit('screen_share', this.checked);
    });
  }

  // Action timeline controls
  const tlQ = document.getElementById('tlQ');
  const tlF = document.getElementById('tlF');
  const tlClr = document.getElementById('tlClr');

  if (tlQ) tlQ.addEventListener('input', renderTL);
  if (tlF) {
    tlF.addEventListener('change', () => {
      sfx.blip();
      renderTL();
    });
  }
  if (tlClr) {
    tlClr.addEventListener('click', () => {
      if (confirm('Clear the timeline?')) {
        TL = [];
        tlSave();
        renderTL();
        sfx.del();
        emit('timeline_clear');
      }
    });
  }

  // Command palette inputs & events
  const palIn = document.getElementById('palIn');
  const palList = document.getElementById('palList');

  if (palIn) {
    palIn.addEventListener('input', () => {
      palSel = 0;
      renderPalette();
    });

    palIn.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') {
        sfx.nav();
        palSel = Math.min(palItems.length - 1, palSel + 1);
        renderPalette();
        e.preventDefault();
      } else if (e.key === 'ArrowUp') {
        sfx.nav();
        palSel = Math.max(0, palSel - 1);
        renderPalette();
        e.preventDefault();
      } else if (e.key === 'Enter') {
        runPaletteItem(palSel);
      } else if (e.key === 'Escape') {
        closeM();
      }
    });
  }

  if (palList) {
    palList.addEventListener('click', e => {
      const p = e.target.closest('.pi');
      if (p && p.dataset.i != null) runPaletteItem(+p.dataset.i);
    });
  }

  // Ctrl+K / Cmd+K listener for Command Palette
  window.addEventListener('keydown', e => {
    const modal = document.querySelector('.modal.o');
    if (modal && e.key === 'Tab') {
      const controls = modalControls(modal);
      const first = controls[0] || modal, last = controls.at(-1) || modal;
      if (!modal.contains(document.activeElement) || (e.shiftKey && document.activeElement === first) || (!e.shiftKey && document.activeElement === last)) {
        e.preventDefault();
        (e.shiftKey ? last : first).focus();
      }
    }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openM('mPal');
      setTimeout(() => {
        if (palIn) {
          palIn.value = '';
          renderPalette();
          palIn.focus();
        }
      }, 60);
    }
  });

  // Expose global window hooks for compatibility
  window.openM = openM;
  window.closeM = closeM;
  window.toggleD = toggleD;
}
