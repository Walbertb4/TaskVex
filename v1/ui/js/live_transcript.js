/** Tek Live isteğinin kullanıcı/model metnini aynı iki balonda günceller.
 * Backend birikimli snapshot yollar; sıra numarası tekrarları, istek kimliği
 * eski turu reddeder. Kesilen metin korunur; bu durum araç başarısı değildir.
 */
let current = null;
const labels = {live:' · Live', interrupted:' · Interrupted', failed:' · Incomplete', unknown:' · Result unknown', complete:''};

function render(role, value, status) {
  const state = current, panel = document.getElementById('msgs');
  if (!state || !panel || !value || role === 'u' && state.typed) return;
  let node = state.nodes[role];
  if (!node) {
    const element = document.createElement('div'), body = document.createElement('span'), label = document.createElement('small');
    element.className = 'm ' + role; element.dataset.requestId = state.id;
    label.className = 'transcript-status'; element.append(body, label);
    // Sağlayıcı giriş transkriptini daha geç iletse de kullanıcı sözü kendi
    // yanıtının önünde kalır; başka turun balonları taşınmaz.
    if (role === 'u' && state.nodes.j?.element.parentNode === panel) panel.insertBefore(element, state.nodes.j.element);
    else panel.append(element);
    node = state.nodes[role] = {element, body, label};
  }
  node.body.textContent = (role === 'u' ? '› ' : '') + value;
  node.label.textContent = labels[status]; node.element.dataset.state = status;
  panel.scrollTop = panel.scrollHeight;
}

export const liveTranscript = {
  begin(requestId, typed = false) { current = {id:requestId, typed, nodes:{}, sequence:0, frozen:false}; },
  chunk(packet) {
    const s = current;
    if (!s || packet?.request_id !== s.id || !['u','j'].includes(packet.role) ||
        !Number.isSafeInteger(packet.sequence) || packet.sequence <= s.sequence ||
        typeof packet.text !== 'string' || packet.text.length > (packet.role === 'u' ? 20000 : 32000)) return false;
    s.sequence = packet.sequence;
    if (!(s.frozen && packet.role === 'j')) render(packet.role, packet.text, 'live');
    return true;
  },
  interrupt(requestId) {
    if (current?.id !== requestId) return;
    current.frozen = true;
    const node = current.nodes.j;
    if (node) { node.label.textContent = labels.interrupted; node.element.dataset.state = 'interrupted'; }
  },
  finish(requestId, report = {}, status = 'complete') {
    if (current?.id !== requestId) return false;
    // Ekran bildirimi başarısızsa son rapor yedektir. Kesilmiş çıktı daha
    // sonra üretilmiş metinle genişletilmez, ikinci balon oluşturulmaz.
    if (typeof report.input_text === 'string' && report.input_text.length <= 20000) render('u', report.input_text, status);
    if (!current.frozen && typeof report.text === 'string' && report.text.length <= 32000) render('j', report.text, status);
    for (const [role, node] of Object.entries(current.nodes)) {
      const finalStatus = role === 'j' && current.frozen && status === 'complete' ? 'interrupted' : status;
      node.label.textContent = labels[finalStatus]; node.element.dataset.state = finalStatus;
    }
    current = null;
    return true;
  }
};
