/** Yerel sistem görünümünü ortak UI tick'inden yeniler; ölçümün sahibi Python'dur.
 * Ayrı örnekleyici/thread veya görev mutasyonu yoktur. Ağ/model durumu bu yerel
 * ölçümleri silmez; gecikmiş/başarısız ölçüm güncelmiş gibi gösterilmez. */
import {emit,isBackendAvailable} from './api.js';
import {setTelemetry,setNetwork} from './connections.js';
let started=false,pending=false,closed=false,lastAttempt=-Infinity,lastSuccess=-Infinity,sample=-Infinity;
window.addEventListener('pagehide',()=>{closed=true;},{once:true});
const finite=(value,min=0,max=Infinity)=>typeof value==='number'&&Number.isFinite(value)&&value>=min&&value<=max;
const optional=(value,check)=>value==null||check(value);
const gib=value=>(value/1073741824).toFixed(1);

export function applySystemSample(data) {
  if(!data||!finite(data.sampled_at)||data.sampled_at<sample)return false;
  if(!['cpu_percent','memory_percent','gpu_percent','battery_percent'].every(k=>optional(data[k],v=>finite(v,0,100)))||
     !['memory_used','memory_total','disk_used','disk_total'].every(k=>optional(data[k],v=>finite(v)))||
     !['cpu_temperature','gpu_temperature'].every(k=>optional(data[k],v=>finite(v,0,150)))||
     !['network_receive_bps','network_send_bps'].every(k=>optional(data[k],v=>finite(v)))||
     !['network_link','network_wifi_connected'].every(k=>optional(data[k],v=>typeof v==='boolean'))||
     !optional(data.network_kind,v=>['wifi','ethernet','other','multiple'].includes(v))||
     !['active_process','disk_volume'].every(k=>optional(data[k],v=>typeof v==='string'&&v.length<=260)))return false;
  sample=data.sampled_at;
  const memory=finite(data.memory_used)&&finite(data.memory_total)&&data.memory_total>0;
  const disk=finite(data.disk_used)&&finite(data.disk_total)&&data.disk_total>0;
  setTelemetry({cpu:data.cpu_percent??null,ram:data.memory_percent??null,gpu:data.gpu_percent??null,
    cpuT:data.cpu_temperature??null,gpuT:data.gpu_temperature??null,
    ramTxt:memory?`${gib(data.memory_used)} / ${gib(data.memory_total)} GiB`:null,
    bat:data.battery_present===false?'No battery':data.battery_percent==null?null:
      `${data.battery_percent}%${data.ac_connected===true?' · AC':''}`,
    disk:disk?`${data.disk_volume??''} ${gib(data.disk_used)} / ${gib(data.disk_total)} GiB`:null,
    win:data.active_process??null});
  setNetwork({down:data.network_receive_bps==null?null:data.network_receive_bps*8/1000000,
    up:data.network_send_bps==null?null:data.network_send_bps*8/1000000,
    link:data.network_link===false?'disconnected':data.network_link===true?(data.network_kind??'other'):null,
    wifiConnected:data.network_wifi_connected??null});
  const gpuValue=document.getElementById('gpu');
  if(gpuValue)gpuValue.title=data.gpu_percent==null?'Windows GPU counters unavailable':
    'Windows GPU usage · busiest engine across adapters · sampled interval';
  for(const id of ['cpuT','gpuT']) {
    const el=document.getElementById(id);
    if(el)el.title='Temperature: no supported system sensor source';
  }
  return true;
}

export function startSystemView() {started=true;void refreshSystem();}

export async function refreshSystem() {
  if(!started||closed||!isBackendAvailable())return;
  const now=performance.now();
  if(now-(lastSuccess===-Infinity?lastAttempt:lastSuccess)>12000&&lastAttempt!==-Infinity) {
    setTelemetry(null);
    setNetwork({down:null,up:null,link:null,wifiConnected:null});
  }
  if(pending||now-lastAttempt<3000)return;
  pending=true;lastAttempt=now;
  try {
    const result=await emit('query_system');
    if(closed)return;
    if(result.ok&&result.response?.completed===true&&applySystemSample(result.response.data))lastSuccess=performance.now();
    else {
      setTelemetry(null);
      setNetwork({down:null,up:null,link:null,wifiConnected:null});
    }
  } finally {pending=false;}
}
