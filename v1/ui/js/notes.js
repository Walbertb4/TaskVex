/**
 * Not görünümü ve kullanıcı eylemleri. Tarayıcıda yerel mod korunur; native
 * modda tek kalıcı sahip backend'dir. İlk aktarım açık kullanıcı onayı ister.
 * Başarı gelmeden liste değiştirilmez; belirsiz işlem otomatik gönderilmez.
 */
import { sfx } from './sfx.js';
import { emit, isBackendAvailable, createPendingOperation, sanitizeError } from './api.js';
import { uniqueRecordId, validNoteCreatedAt } from './schema.js';

let notes = [], saveStoreCb = null, addTimelineCb = null;
let mode = 'local', busy = false, importLocked = false, chatLocked = false, status = '';
const pending = createPendingOperation(() => {
  busy = false;
  mode = 'unknown';
  status = 'Notes were not confirmed. Close and reopen the app before retrying.';
  renderNotes();
});

export function getNotes() { return notes; }

function normalize(list) {
  return (Array.isArray(list) ? list : []).map(item => typeof item === 'string'
    ? { t: item, d: 0 }
    : { ...(typeof item?.id === 'string' ? { id: item.id } : {}),
        ...(item?.created_at !== undefined && validNoteCreatedAt(item.created_at) ? { created_at: item.created_at } : {}),
        t: String(item?.t ?? ''), d: item?.d ? 1 : 0 });
}

/** Native kayıtlar görünüm biçimine çevrilir; id aktarımda asla düşürülmez. */
function acceptNative(list) {
  if (!Array.isArray(list) || list.some(n => !n || typeof n.id !== 'string' || !n.id.trim() ||
      typeof n.text !== 'string' || typeof n.done !== 'boolean' || !validNoteCreatedAt(n.created_at)) ||
      new Set(list.map(n => n.id)).size !== list.length) throw new Error('Invalid native notes');
  notes = list.map(n => ({ id: n.id, t: n.text, d: n.done ? 1 : 0,
    ...(n.created_at !== undefined ? { created_at: n.created_at } : {}) }));
}

/** Yerel kopya yalnız önbellek/yedek içindir; yazılamaması backend başarısını silmez. */
function cacheNative() {
  if (saveStoreCb && saveStoreCb({ emitSave: false }) === false)
    status = 'Notes saved in backend; local backup cache could not be saved.';
}

async function nativeCommand(name, args) {
  if (busy || mode === 'unknown') return false;
  busy = true;
  status = name === 'notes_init' ? 'Loading notes…' : 'Saving note…';
  renderNotes();
  const revision = pending.begin();
  const result = await emit(name, {
    version: 1, request_id: uniqueRecordId([], 'note_request'), arguments: args
  });
  if (!pending.isCurrent(revision)) return false;
  pending.finish();
  busy = false;
  if (!result.ok || result.response?.completed !== true || result.response?.verified !== true) {
    if (!result.response || result.response.unknown || result.ok) mode = 'unknown';
    status = mode === 'unknown' ? 'Note result is unknown. Close and reopen the app before retrying.'
      : 'Notes: ' + sanitizeError(result.error || result.response?.error || 'Not saved');
    renderNotes();
    return false;
  }
  try {
    const data = result.response.data;
    if (name === 'notes_init' || name === 'notes_replace') {
      if (typeof data?.migrated !== 'boolean') throw new Error('Missing migration state');
      if (!data.migrated) {
        mode = 'transfer';
        status = 'Local notes are preserved. Confirm transfer to use backend notes.';
        renderNotes();
        return true;
      }
      acceptNative(data.notes);
      mode = 'native';
    } else {
      const note = data?.note;
      if (!note || typeof note.id !== 'string') throw new Error('Missing note result');
      if ((name !== 'note_add' && note.id !== args.id) ||
          (name === 'note_done' && note.done !== args.done) ||
          (name === 'note_add' && note.text !== args.text)) throw new Error('Note result does not match request');
      const current = notes.map(n => ({ id: n.id, text: n.t, done: !!n.d,
        ...(n.created_at !== undefined ? { created_at: n.created_at } : {}) }));
      if (name === 'note_add') acceptNative([...current, note]);
      else if (name === 'note_done') acceptNative(current.map(n => n.id === note.id ? note : n));
      else acceptNative(current.filter(n => n.id !== note.id));
    }
    status = 'Notes saved in backend';
    cacheNative();
    renderNotes();
    return true;
  } catch (error) {
    mode = 'unknown';
    status = 'Invalid note confirmation. Close and reopen the app before retrying.';
    renderNotes();
    return false;
  }
}

/** El sıkışması tamamlanınca önce salt okunur durum sorgulanır; otomatik aktarım yok. */
export function connectNativeNotes() {
  if (!isBackendAvailable()) return false;
  if (mode === 'local') mode = 'waiting';
  return nativeCommand('notes_init', { notes: null });
}

/** İçe aktarım sırasında not işlemleri başka bir kayıtla yarışmasın. */
export function setNotesImportLock(locked) { importLocked = locked; renderNotes(); }
/** Model not yazarken kullanıcı mutasyonu/import başlatmasın; ayrı kilit sahipliği. */
export function setNotesChatLock(locked) { chatLocked = locked; renderNotes(); }
export function canRestoreNativeNotes() { return mode === 'native' && !busy && !importLocked && !chatLocked; }
/** İlk aktarım beklerken sohbet açıktır; süren/belirsiz not yazımıyla yarışılmaz. */
export function canSendNativeText() { return !busy && !importLocked && !chatLocked && mode !== 'unknown'; }

/** Açık yedek yükleme komutu; eski kimliksiz kayıtlara yalnız burada kimlik üret. */
export function restoreNativeNotes(list) {
  if (mode !== 'native' || busy || chatLocked) return false;
  const records = normalize(list);
  const used = records.filter(n => n.id);
  const incoming = records.map(n => {
    const id = n.id || uniqueRecordId(used, 'note');
    used.push({ id });
    return { id, text: n.t, done: !!n.d,
      ...(n.created_at !== undefined ? { created_at: n.created_at } : {}) };
  });
  return nativeCommand('notes_replace', { notes: incoming });
}

export function renderNotes() {
  const container = document.getElementById('notes');
  if (!container) return;
  const disabled = busy || importLocked || chatLocked || !['local', 'native'].includes(mode);
  for (const id of ['noteIn', 'noteAdd']) {
    const element = document.getElementById(id);
    if (element) element.disabled = disabled;
  }
  const label = document.getElementById('notesStatus');
  if (label) { label.textContent = status; label.hidden = !status; }
  const connect = document.getElementById('notesConnect');
  if (connect) {
    connect.hidden = !['waiting', 'transfer'].includes(mode);
    connect.disabled = busy || importLocked;
    connect.textContent = mode === 'transfer' ? 'Use backend notes' : 'Retry notes';
  }
  container.replaceChildren();
  if (!notes.length) {
    const empty = document.createElement('div');
    empty.className = 'sub';
    empty.style.textTransform = 'none';
    empty.textContent = 'No notes.';
    container.append(empty);
    return;
  }
  notes.forEach((n, i) => {
    const row = document.createElement('div');
    row.className = 'nt' + (n.d ? ' d' : '');
    if (n.id) row.dataset.noteId = n.id;
    const cb = document.createElement('input');
    cb.type = 'checkbox'; cb.checked = !!n.d; cb.disabled = disabled;
    cb.dataset.i = String(i);
    cb.addEventListener('change', async e => {
      const done = e.target.checked;
      if (mode === 'native') {
        // Tarayıcının checkbox değişimini geri al; yalnız kesin sonuç uygulansın.
        cb.checked = !!n.d;
        if (await nativeCommand('note_done', { id: n.id, done })) sfx.check();
        return;
      }
      notes[i].d = done ? 1 : 0;
      sfx.check(); renderNotes();
      saveStoreCb?.({ emitSave: false }); emit('note_done', notes[i]);
    });
    const span = document.createElement('span'); span.textContent = n.t;
    const del = document.createElement('button');
    del.className = 'ib'; del.textContent = '✕'; del.disabled = disabled;
    del.dataset.i = String(i);
    del.addEventListener('click', async () => {
      if (mode === 'native') {
        if (await nativeCommand('note_del', { id: n.id })) sfx.del();
        return;
      }
      const removed = notes.splice(i, 1)[0];
      sfx.del(); renderNotes();
      saveStoreCb?.({ emitSave: false }); emit('note_del', removed.t);
    });
    row.append(cb, span, del); container.append(row);
  });
}

export function addNote(text, options = {}) {
  const silent = typeof options === 'boolean' ? options : !!options.silent;
  const fromUser = typeof options === 'object' && options.fromUser !== undefined ? !!options.fromUser : !silent;
  const t = String(text || '').trim();
  if (!t || busy || importLocked || chatLocked) return false;
  if (mode !== 'local') {
    if (mode !== 'native' || !fromUser) return false;
    return nativeCommand('note_add', { text: t }).then(ok => {
      if (ok) { sfx.add(); addTimelineCb?.('Note added: ' + t, true, 'note'); }
      return ok;
    });
  }
  notes.push({ t, d: 0, created_at: new Date().toISOString() });
  if (fromUser) { sfx.add(); addTimelineCb?.('Note added: ' + t, true, 'note'); }
  renderNotes();
  document.getElementById('notes')?.lastElementChild?.classList.add('new');
  saveStoreCb?.({ emitSave: false });
  if (fromUser && !silent) emit('note_add', t);
  return true;
}

/** Native modda eski setter kalıcı otoriteyi atlayamaz; yanıtlar içeriden uygulanır. */
export function setNotes(list, options = {}) {
  if (mode !== 'local') return false;
  notes = normalize(list); renderNotes();
  if (!options.silent) saveStoreCb?.({ emitSave: !!options.emitSave });
  return true;
}

export function initNotes(options = {}) {
  notes = normalize(options.initialNotes);
  saveStoreCb = options.saveStore || null;
  addTimelineCb = options.addTimeline || null;
  mode = isBackendAvailable() ? 'waiting' : 'local';
  window.addEventListener('pywebviewready', () => {
    if (mode === 'local') { mode = 'waiting'; renderNotes(); }
  }, { once: true });
  const input = document.getElementById('noteIn'), add = document.getElementById('noteAdd');
  if (add && input) {
    add.addEventListener('click', async () => {
      const text = input.value;
      if (await addNote(text, { fromUser: true }) && input.value === text) input.value = '';
    });
    input.addEventListener('keydown', e => { if (e.key === 'Enter') add.click(); });
  }
  document.getElementById('notesConnect')?.addEventListener('click', async () => {
    if (mode !== 'transfer') { await connectNativeNotes(); return; }
    if (!window.confirm('Transfer local notes to the backend? Existing backend notes will be kept. This runs only once.')) return;
    await nativeCommand('notes_init', { notes: notes.map(n => ({ text: n.t, done: !!n.d,
      ...(n.created_at !== undefined ? { created_at: n.created_at } : {}) })) });
  });
  renderNotes();
}
