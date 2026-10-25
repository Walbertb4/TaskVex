/** Visual resource owner: one opt-in camera or screen, bounded JPEGs, one Live request.
 * Idle pixels stay local. The assistant lifecycle starts/ends transmission; this
 * module never opens a model connection, records a file or executes a tool. */
import {emit, addLog} from './api.js';

let current = null, turn = null;
function release(state) {
  clearTimeout(state.timer);
  state.stream?.getTracks().forEach(track => { track.onended = null; track.stop(); });
  state.video.pause(); state.video.srcObject = null;
}
function paint() {
  const button = document.getElementById('camB');
  const camera = current?.source === 'camera', screen = current?.source === 'screen';
  const active = camera && !!current.ready;
  if (button) {
    button.classList.toggle('on', active);
    button.setAttribute('aria-pressed', String(active));
    button.lastChild.textContent = camera ? active ? 'Camera On' : 'Cancel camera…' : 'Camera Off';
    button.title = active ? 'Camera ready; images are shared only during Live messages. Click to turn off.' : 'Enable camera for Live messages; never opens automatically.';
  }
  const toggle = document.getElementById('scrT'), status = document.getElementById('screenStatus');
  if (toggle) toggle.checked = screen;
  if (status) status.textContent = screen ? current.ready
    ? 'Screen ready. Images are shared only during Live messages; system audio is off.'
    : 'Choose a screen or window. Turn sharing off to cancel.' : 'Screen sharing is off. Select a source each time.';
  const preview = document.getElementById('scr');
  if (preview) preview.replaceChildren(...(screen && current.ready ? [current.video] : ['Screen sharing is off.']));
  const opener = document.getElementById('btnOpenScreen');
  if (opener) { opener.classList.toggle('on', screen); opener.setAttribute('aria-pressed', String(screen)); }
}

export const liveVideo = {
  get active() { return !!current?.ready; },
  get opening() { return !!current && !current.ready; },
  get source() { return current?.source || null; },
  async start(deviceId = '', source = 'camera') {
    if (!['camera','screen'].includes(source)) return false;
    if (current) return;
    const name = source === 'screen' ? 'Screen sharing' : 'Camera';
    const state = current = {source, stream:null, video:document.createElement('video'), timer:null, ready:false};
    state.video.muted = true; state.video.playsInline = true;
    paint();
    // Permission can resolve after timeout/Off. Its late stream must still be released.
    try {
      // getDisplayMedia must run synchronously from the user's click, before any await.
      const capture = source === 'screen' ? navigator.mediaDevices.getDisplayMedia({audio:false, video:{frameRate:{ideal:1,max:1}}})
        : navigator.mediaDevices.getUserMedia({audio:false, video:{
        width:{ideal:640}, height:{ideal:480}, frameRate:{ideal:1, max:1},
        ...(deviceId ? {deviceId:{exact:deviceId}} : {})
      }});
      const permission = capture.then(stream => {
        state.stream = stream;
        if (current !== state) { release(state); return false; }
        if (stream.getVideoTracks().length !== 1 || stream.getAudioTracks().length) throw new Error('Unexpected visual tracks');
        state.video.srcObject = stream;
        stream.getTracks().forEach(track => { track.onended = () => {
          if (current === state) { this.stop(); addLog(name + ' ended. Select the source again to continue.', true); }
        }; });
        return state.video.play();
      });
      await Promise.race([permission, new Promise((_, reject) => {
        state.timer = setTimeout(() => reject(new Error('Visual permission/setup timed out.')), 15000);
      })]);
      if (current !== state) return false;
      if (!state.video.videoWidth || !state.video.videoHeight) throw new Error('Visual source has no image.');
      clearTimeout(state.timer); state.ready = true; paint(); return true;
    } catch {
      release(state);
      if (current !== state) return false;
      current = null; paint();
      addLog(name + ' unavailable, cancelled or permission denied. Check browser/Windows support, then select the source again.', true);
      return false;
    }
  },
  stop() {
    this.endTurn();
    const state = current; current = null;
    if (state) release(state);
    paint();
  },
  snapshot() {
    if (!this.active) return null;
    const video = current.video;
    if (video.readyState < 2 || !video.videoWidth || !video.videoHeight) throw new Error('Visual image unavailable');
    const canvas = document.createElement('canvas');
    const edge = current.source === 'screen' ? 1280 : 640;
    const scale = Math.min(1, edge / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
    canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    const image = canvas.toDataURL('image/jpeg', .65);
    if (!image.startsWith('data:image/jpeg;base64,') || image.length > 349551) throw new Error('Visual image exceeds limit');
    return image.slice(23);
  },
  endTurn(requestId = null, notify = true) {
    const state = turn;
    if (!state || requestId && state.id !== requestId) return;
    turn = null; clearTimeout(state.timer);
    // Serialize closure after an already in-flight frame. Off never cancels audio/reply.
    if (notify) void state.delivery.then(() => emit('live_video_feed', {request_id:state.id, sequence:state.sequence++, data:null}));
  },
  async withInput(requestId, send) {
    let initial;
    try { initial = this.snapshot(); }
    catch { this.stop(); addLog('Visual image unavailable; this message has no visual input.', true); }
    if (!initial) return send({});
    const state = turn = {id:requestId, sequence:0, timer:null, delivery:Promise.resolve()};
    const pump = async () => {
      if (turn !== state || !this.active) return;
      try {
        state.delivery = emit('live_video_feed', {request_id:requestId});
        const status = await state.delivery;
        if (turn !== state) return;
        if (status.response?.closed) { this.endTurn(requestId, false); return; }
        if (status.ok && status.response?.ready) {
          const data = this.snapshot();
          state.delivery = emit('live_video_feed', {request_id:requestId, sequence:state.sequence++, data});
          const ack = await state.delivery;
          if (turn !== state) return;
          if (!ack.ok) throw new Error('Visual input rejected');
        }
      } catch {
        if (turn === state) { this.stop(); addLog('Visual transmission stopped; audio and the current reply were preserved.', true); }
      }
      if (turn === state) state.timer = setTimeout(pump, 1000);
    };
    state.timer = setTimeout(pump, 1000);
    try { return await send({video:initial}); }
    finally { this.endTurn(requestId, false); }
  }
};
window.addEventListener('pagehide', () => liveVideo.stop());
