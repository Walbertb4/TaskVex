/** Widget order/size and compact appearance editor.
 * The layout preference is in the single preferences.store object, the record is in the settings.js line. */
import {store} from './preferences.js';
import {LD} from './schema.js';
import {sfx} from './sfx.js';
let saveLayout = () => false;
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
  saveLayout();
}

export function updateCompactView() {
  const cmpSel = document.getElementById('cmpSel');
  const m = (cmpSel && cmpSel.value) || store.cmp || 'auto';
  document.body.classList.toggle(
    'compact',
    m === 'on' || (m === 'auto' && (window.innerWidth < 900 || window.innerHeight < 620))
  );
}


export function initLayoutSettings(save) {
  saveLayout = save;
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

}
