/**
 * API anahtarının yalnız native kimlik deposuna kaydı ve sır içermeyen durum.
 * Anahtar store/localStorage/yedeğe girmez. Kayıt onayı API erişim onayı değildir.
 */
import { emit, isBackendAvailable, createPendingOperation } from './api.js';
import { sfx } from './sfx.js';

export function initCredentials() {
  const input = document.getElementById('apiKeyIn');
  const button = document.getElementById('saveApiKey');
  const message = document.getElementById('apiKeyStatus');
  if (!input || !button || !message) return;
  let statusRevision = 0;

  const operation = createPendingOperation(() => {
    message.textContent = 'Key save not confirmed. Restart the app to check storage; the request will not be repeated.';
  });

  async function refresh() {
    const revision = ++statusRevision;
    if (!isBackendAvailable()) {
      message.textContent = 'Key storage requires the desktop app.';
      return;
    }
    const result = await emit('query_apikey');
    if (revision !== statusRevision || operation.pending || operation.uncertain) return;
    message.textContent = result.ok && result.response?.completed === true
      ? (result.response.configured ? 'Key stored locally. API access has not been checked.' : 'No key stored for this profile.')
      : 'Could not check Windows key storage.';
  }

  async function save() {
    if (operation.pending || operation.uncertain) return;
    const key = input.value;
    input.value = ''; // Gizli girdi bekleyen Promise süresince DOM'da kalmasın.
    if (!isBackendAvailable()) { message.textContent = 'Key storage requires the desktop app.'; return; }
    if (!key.trim()) { message.textContent = 'Enter an API key.'; return; }
    statusRevision++; // Kaydetmeden önce başlayan sorgu yeni kayıt durumunu ezmesin.
    const id = operation.begin();
    input.disabled = button.disabled = true;
    message.textContent = 'Saving to Windows credentials…';
    const result = await emit('apikey', key);
    if (!operation.isCurrent(id)) return;
    if (result.ok && (result.response?.completed !== true || result.response?.saved !== true || result.response?.configured !== true)) {
      operation.markUnknown();
      return;
    }
    operation.finish();
    input.disabled = button.disabled = false;
    message.textContent = result.ok ? 'Key stored locally. API access has not been checked.'
      : 'Key save was not confirmed. Check Windows credentials before trying again.';
    if (result.ok) {
      sfx.ok();
      window.dispatchEvent(new Event('taskvex-key-saved'));
    }
  }

  button.addEventListener('click', save);
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter') { event.preventDefault(); event.stopPropagation(); save(); }
  });
  window.addEventListener('pywebviewready', refresh, { once: true });
  refresh();
}
