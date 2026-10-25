/** Camera resource owner: opt-in browser capture, bounded JPEGs, one Live request.
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
  if (!button) return;
  const active = !!current?.ready;
  button.classList.toggle('on', active);
  button.setAttribute('aria-pressed', String(active));
  button.lastChild.textContent = current ? active ? 'Camera On' : 'Cancel camera…' : 'Camera Off';
  button.title = active ? 'Camera ready; images are shared only during Live messages. Click to turn off.' : 'Enable camera for Live messages; never opens automatically.';
}

export const liveVideo = {
  get active() { return !!current?.ready; },
  get opening() { return !!current && !current.ready; },
  async start(deviceId = '') {
    if (current) return;
    const state = current = {stream:null, video:document.createElement('video'), timer:null, ready:false};
    state.video.muted = true; state.video.playsInline = true;
    paint();
    // Permission can resolve after timeout/Off. Its late stream must still be released.
    try {
      const permission = navigator.mediaDevices.getUserMedia({audio:false, video:{
        width:{ideal:640}, height:{ideal:480}, frameRate:{ideal:1, max:1},
        ...(deviceId ? {deviceId:{exact:deviceId}} : {})
      }}).then(stream => {
        state.stream = stream;
        if (current !== state) { release(state); return false; }
        state.video.srcObject = stream;
        stream.getTracks().forEach(track => { track.onended = () => {
          if (current === state) { this.stop(); addLog('Camera disconnected. Enable it again after checking the device.', true); }
        }; });
        return state.video.play();
      });
      await Promise.race([permission, new Promise((_, reject) => {
        state.timer = setTimeout(() => reject(new Error('Camera permission/setup timed out.')), 15000);
      })]);
      if (current !== state) return false;
      if (!state.video.videoWidth || !state.video.videoHeight) throw new Error('Camera has no image.');
      clearTimeout(state.timer); state.ready = true; paint(); return true;
    } catch {
      release(state);
      if (current !== state) return false;
      current = null; paint();
      addLog('Camera unavailable or permission denied. Check Windows/device permissions, then enable it again.', true);
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
    if (video.readyState < 2 || !video.videoWidth || !video.videoHeight) throw new Error('Camera image unavailable');
    const canvas = document.createElement('canvas');
    const scale = Math.min(1, 640 / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
    canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    const image = canvas.toDataURL('image/jpeg', .65);
    if (!image.startsWith('data:image/jpeg;base64,') || image.length > 349551) throw new Error('Camera image exceeds limit');
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
    catch { this.stop(); addLog('Camera image unavailable; this message has no camera input.', true); }
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
          if (!ack.ok) throw new Error('Camera input rejected');
        }
      } catch {
        if (turn === state) { this.stop(); addLog('Camera transmission stopped; audio and the current reply were preserved.', true); }
      }
      if (turn === state) state.timer = setTimeout(pump, 1000);
    };
    state.timer = setTimeout(pump, 1000);
    try { return await send({video:initial}); }
    finally { this.endTurn(requestId, false); }
  }
};
window.addEventListener('pagehide', () => liveVideo.stop());
