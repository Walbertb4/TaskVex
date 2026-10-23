"""Gerçek Windows/WebView2 kabul kontrolü: python tests/native_smoke.py.

pytest'e dahil değildir; gerçek native motor gerektirir. Ana süreç geçici bir
TASKVEX_HOME oluşturur; aç/kaydet, kayıt-import-export, iptal ve ayar-hatası
ve not CRUD/kimlik deposu/metin senaryolarını on ayrı süreçte çalıştırır. Pencereler hidden'dır. Kullanıcı
verisi kullanılmaz; test sonunda geçici profil/veri dizini temizlenir.
"""

import argparse
import faulthandler
import json
import os
import socket
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Event
import time
import traceback

# Betik tests/ içinden doğrudan çalıştırıldığında app paketi de bulunmalıdır.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def check_native_note_ui(home, window, js, wait_until, outcome):
    """Not panelinin yerel CRUD, gecikmiş yanıt ve kayıt reddi senaryosu."""
    from app.storage.json_store import StoreError
    # Gerçek UI kontrolleri -> köprü -> worker -> gerçek dosya.
    js("document.getElementById('noteIn').value='Duplicate';document.getElementById('noteAdd').click();return true;")
    wait_until(lambda: len(json.loads((home / 'notes.json').read_text('utf-8'))['data']['notes']) == 2)
    wait_until(lambda: not window.evaluate_js("document.getElementById('noteAdd').disabled"))
    js("document.getElementById('noteIn').value='Duplicate';document.getElementById('noteAdd').click();return true;")
    wait_until(lambda: len(json.loads((home / 'notes.json').read_text('utf-8'))['data']['notes']) == 3)
    wait_until(lambda: not window.evaluate_js("document.getElementById('noteAdd').disabled"))
    saved = json.loads((home / 'notes.json').read_text('utf-8'))['data']['notes']
    assert len({note['id'] for note in saved}) == 3
    created_at = saved[1]["created_at"]
    assert created_at and js("const n=await import('./js/notes.js');return n.getNotes()[1].created_at;") == created_at
    js("document.querySelectorAll('#notes input')[1].click();return true;")
    wait_until(lambda: json.loads((home / 'notes.json').read_text('utf-8'))['data']['notes'][1]['done'])
    wait_until(lambda: not window.evaluate_js("document.getElementById('noteAdd').disabled"))
    assert js("const n=await import('./js/notes.js');return n.getNotes()[1].created_at;") == created_at
    js("document.querySelectorAll('#notes button')[1].click();return true;")
    wait_until(lambda: len(json.loads((home / 'notes.json').read_text('utf-8'))['data']['notes']) == 2)
    wait_until(lambda: not window.evaluate_js("document.getElementById('noteAdd').disabled"))
    assert json.loads((home / 'notes.json').read_text('utf-8'))['data']['notes'][1]['id'] == saved[2]['id']
    js("document.querySelectorAll('#notes button')[1].click();return true;")
    wait_until(lambda: not window.evaluate_js("document.getElementById('noteAdd').disabled"))
    # Yazma reddinde form metni ve liste korunmalı.
    from app.storage.json_store import JsonStore
    original_write = JsonStore.write

    def fail_note(self, data):
        if self.path.name == 'notes.json':
            raise StoreError('write_failed', 'Simulated note failure')
        return original_write(self, data)

    JsonStore.write = fail_note
    try:
        js("document.getElementById('noteIn').value='Keep input';document.getElementById('noteAdd').click();return true;")
        wait_until(lambda: not window.evaluate_js("document.getElementById('noteAdd').disabled"))
        assert window.evaluate_js("document.getElementById('noteIn').value") == 'Keep input'
        assert len(json.loads((home / 'notes.json').read_text('utf-8'))['data']['notes']) == 1
    finally:
        JsonStore.write = original_write
    assert js("return window.vex.initApp({notes:['Must not overwrite']});") is False
    assert js("const n=await import('./js/notes.js');return await n.addNote('No echo',{fromUser:false,silent:true});") is False
    # Yan etki gerçekten olur; yalnız UI yanıtı geciktirilir. Deadline
    # sonrası geç yanıt UI'ı değiştiremez veya ikinci komut üretemez.
    js("window._noteSends=0;const original=window.pywebview.api.event;"
       "window.pywebview.api.event=async(name,data)=>{if(name!=='note_add')return original(name,data);"
       "window._noteSends++;const response=await original(name,data);await new Promise(r=>setTimeout(r,13000));return response;};"
       "document.getElementById('noteIn').value='Late note';document.getElementById('noteAdd').click();document.getElementById('noteAdd').click();return true;")
    wait_until(lambda: 'not confirmed' in window.evaluate_js("document.getElementById('notesStatus').textContent"))
    time.sleep(1.5)
    assert window.evaluate_js("document.getElementById('noteAdd').disabled")
    assert window.evaluate_js("window._noteSends") == 1
    assert 'Late note' not in window.evaluate_js("document.getElementById('notes').textContent")
    assert [n['text'] for n in json.loads((home / 'notes.json').read_text('utf-8'))['data']['notes']] == ['Native local note', 'Late note']
    outcome.update(ok=True, phase="notes", real_ui_crud=True, duplicate_text_ids=True, note_time_preserved=True,
                   write_rejection_preserved_input=True, snapshot_cannot_overwrite_notes=True,
                   double_click_one_command=True, timeout_late_reply_ignored=True)
    return


def check_native_note_crud(home, window, js, wait_until, outcome, mode, target):
    """Gerçek gönder düğmesiyle done/edit/delete; UI dosyadan yenilensin."""
    from app.storage.json_store import JsonStore
    snapshot = JsonStore(home / "notes.json").read()
    assert snapshot is not None
    initial = next(n for n in snapshot["notes"] if n["text"] == target)
    assert initial.get("created_at")
    js("window.crudEvents=[];window.crudOriginalEvent=window.pywebview.api.event;"
       "window.pywebview.api.event=(name,data)=>{if(['save','note_add','note_done','note_del'].includes(name))"
       "window.crudEvents.push(name);return window.crudOriginalEvent(name,data);};return true;")
    for verb in ["done", "edit", "delete"]:
        current = target + " edited" if verb == "delete" else target
        selector = ("içinde 'synthetic' geçen notu tamamlandı işaretle" if verb == "done" else
                    "son notu sil" if verb == "delete" else "son notun metnini değiştir")
        prompt = f"Native CRUD {verb}: {current} | {selector}"
        js(f"document.getElementById('inp').value={json.dumps(prompt)};"
           "document.getElementById('send').click();return true;")
        wait_until(lambda: prompt + " confirmed" in window.evaluate_js("document.getElementById('msgs').textContent"))
        wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
        snapshot = JsonStore(home / "notes.json").read()
        assert snapshot is not None
        saved = snapshot["notes"]
        record = next((n for n in saved if n["id"] == initial["id"]), None)
        if verb == "delete":
            assert record is None and current not in window.evaluate_js("document.getElementById('notes').textContent")
        else:
            assert record is not None and record["done"]
            assert record["created_at"] == initial["created_at"]
            assert js("const n=await import('./js/notes.js');return n.getNotes();")[
                next(i for i, n in enumerate(saved) if n["id"] == initial["id"])
            ]["created_at"] == initial["created_at"]
            if verb == "edit":
                assert record["text"] == target + " edited"
            assert record["text"] in window.evaluate_js("document.getElementById('notes').textContent")
            assert window.evaluate_js("!!document.querySelector('#notes .d')")
    assert window.evaluate_js("window.crudEvents") == []
    js("window.pywebview.api.event=window.crudOriginalEvent;return true;")
    outcome[mode + "_model_crud_panel_refreshed"] = True
    outcome[mode + "_model_crud_no_save_echo"] = True
    outcome[mode + "_partial_and_latest_selection"] = True


def check_native_note_batches(api, home, window, js, wait_until, outcome):
    """Geçici notlarda REST/Live toplu silme/tamamlama ve yankısız paneli sına."""
    from app.core.contracts import ToolRequest
    from uuid import uuid4
    # Yalnız geçici native profil: REST ve Live toplu silme gerçek
    # core/worker'dan geçer; panel tek backend okumasıyla yenilenir.
    from app.storage.json_store import JsonStore
    js("window.batchEvents=[];window.batchOriginalEvent=window.pywebview.api.event;window.pywebview.api.event=(name,data)=>{if(['save','note_add','note_done','note_del'].includes(name))batchEvents.push(name);return batchOriginalEvent(name,data);};return true;")
    for batch_mode in ('rest', 'live'):
        data = JsonStore(home/'notes.json').read()
        assert data is not None
        additions = [{'id':f'{batch_mode}-batch-{i}', 'text':f'Batch {i}', 'done':False,
            'created_at':f'2099-01-01T00:00:0{i}.000Z'} for i in (1,2,3)]
        task = api._core.submit(ToolRequest(request_id=uuid4().hex, source='desktop', principal='local-user',
            tool='notes.replace', arguments={'notes':data['notes']+additions}))
        finished = api._core.wait(task.task_id,3)
        assert finished.result is not None and finished.result.verified
        js(f"document.getElementById('liveLatencyTest').checked={str(batch_mode=='live').lower()};return true;")
        for operation in ('latest_done','all_done','all_reopen','latest','all'):
            prompt = 'Native BULK '+operation
            js(f"document.getElementById('inp').value={json.dumps(prompt)};document.getElementById('send').click();return true;")
            wait_until(lambda: prompt+' confirmed' in window.evaluate_js("document.getElementById('msgs').textContent") and not window.evaluate_js("document.getElementById('send').disabled"))
            stored = JsonStore(home/'notes.json').read()
            assert stored is not None
            if operation in ('latest_done', 'all_done', 'all_reopen'):
                target_ids = {n['id'] for n in additions[1:]} if operation == 'latest_done' else {n['id'] for n in stored['notes']}
                expected = [{**n, 'done': operation != 'all_reopen'} if n['id'] in target_ids else n for n in data['notes']+additions]
                assert stored['notes'] == expected
                assert js("const n=await import('./js/notes.js');return n.getNotes().filter(x=>x.d).length;") == sum(n['done'] for n in expected)
                assert window.evaluate_js("document.querySelectorAll('#notes .nt.d').length") == sum(n['done'] for n in expected)
                outcome[batch_mode+'_'+operation+'_preserves_records_and_refreshes_panel'] = True
            elif operation == 'latest':
                assert additions[0] in stored['notes'] and all(n['id'] not in {additions[1]['id'],additions[2]['id']} for n in stored['notes'])
                assert 'Batch 1' in window.evaluate_js("document.getElementById('notes').textContent")
                assert 'Batch 2' not in window.evaluate_js("document.getElementById('notes').textContent")
            else:
                assert stored['notes']==[]
                assert js("const n=await import('./js/notes.js');return n.getNotes().length===0;")
        outcome[batch_mode+'_bulk_latest_and_all_panel_refresh'] = True
    assert window.evaluate_js('window.batchEvents')==[]
    js("window.pywebview.api.event=batchOriginalEvent;document.getElementById('liveLatencyTest').checked=true;return true;")
    outcome['bulk_delete_no_ui_save_echo'] = True


def check_native_clocks(window, api, js, wait_until, outcome):
    """Gerçek sayaç görünümü: model+UI tek ID sahibi ve otomatik sekme odağı."""
    js("window.clockEcho=[];window.clockEvent=window.pywebview.api.event;window.pywebview.api.event=(name,data)=>{if(name==='save')clockEcho.push(name);return clockEvent(name,data);};return true;")
    for mode in ('rest', 'live'):
        js("document.getElementById('liveLatencyTest').checked="+str(mode=='live').lower()+";return true;")
        for action in ('watch', 'timer1', 'timer2', 'pause_timer1', 'reset_watch'):
            # Her model işlemi, diğer sekme açıkken de doğru kayda odaklanmalı.
            js("document.getElementById('"+('tabTmB' if action in ('watch','reset_watch') else 'tabSwB')+"').click();return true;")
            prompt='Native CLOCK '+mode+' '+action
            js("document.getElementById('inp').value="+json.dumps(prompt)+";document.getElementById('send').click();return true;")
            wait_until(lambda: prompt+' confirmed' in window.evaluate_js("document.getElementById('msgs').textContent") and not window.evaluate_js("document.getElementById('send').disabled"))
            kind='stopwatch' if action in ('watch','reset_watch') else 'timer'
            target='timer1' if action=='pause_timer1' else 'watch' if action=='reset_watch' else action
            items=api._clocks.snapshot()['clocks']
            clock=next(c for c in items if c['label']==mode+' '+target)
            assert window.evaluate_js("document.getElementById('clockSelect').value")==clock['id']
            assert window.evaluate_js("document.getElementById('"+('tabSwB' if kind=='stopwatch' else 'tabTmB')+"').classList.contains('on')")
            if action=='pause_timer1':assert clock['state']=='paused'
            if action=='reset_watch':assert clock['state']=='ready' and clock['elapsed_seconds']==0
        assert len([c for c in api._clocks.snapshot()['clocks'] if c['label'].startswith(mode+' ')])==3
        # UI Start/Pause/Resume/Reset aynı stopwatch ID'sini değiştirir, yeni kayıt açmaz.
        watch=next(c for c in api._clocks.snapshot()['clocks'] if c['label']==mode+' watch')
        for button,state in [('swStartB','running'),('swPauseB','paused'),('swResumeB','running'),('swResetB','ready')]:
            js("document.getElementById('"+button+"').click();return true;")
            wait_until(lambda: next(c for c in api._clocks.snapshot()['clocks'] if c['id']==watch['id'])['state']==state)
            wait_until(lambda: not window.evaluate_js("document.getElementById('"+button+"').disabled"))
        timer=next(c for c in api._clocks.snapshot()['clocks'] if c['label']==mode+' timer1')
        js("document.getElementById('tabTmB').click();document.getElementById('clockSelect').value="+json.dumps(timer['id'])+";document.getElementById('clockSelect').dispatchEvent(new Event('change'));document.getElementById('tmMin').value='4';document.getElementById('tmSec').value='5';document.getElementById('tmSetB').click();return true;")
        wait_until(lambda: next(c for c in api._clocks.snapshot()['clocks'] if c['id']==timer['id'])['duration_seconds']==245)
        wait_until(lambda: not window.evaluate_js("document.getElementById('tmSetB').disabled"))
        assert next(c for c in api._clocks.snapshot()['clocks'] if c['id']==timer['id'])['state']=='ready'
        outcome[mode+'_timer_set_preserved_selected_id']=True
        outcome[mode+'_multi_clocks_same_ids_ui_controls_and_automatic_tabs']=True
    assert len(api._clocks.snapshot()['clocks'])==6
    # Gerçek WebView CSS'si tema değişimini izlemeli; profil/veri yazılmaz.
    assert js("const root=document.documentElement,s=document.getElementById('clockSelect'),old=root.style.getPropertyValue('--gold');try{root.style.setProperty('--gold','#12ab34');const a=getComputedStyle(s).color;root.style.setProperty('--gold','#ab3412');return a==='rgb(18, 171, 52)'&&getComputedStyle(s).color==='rgb(171, 52, 18)'&&getComputedStyle(s).appearance==='none'&&getComputedStyle(s).backgroundColor!=='rgb(255, 255, 255)'&&s.getBoundingClientRect().width<=s.closest('.tmin').getBoundingClientRect().width;}finally{if(old)root.style.setProperty('--gold',old);else root.style.removeProperty('--gold');}")
    outcome['clock_selector_webview_theme_and_width']=True
    assert window.evaluate_js('window.clockEcho')==[]
    js("window.pywebview.api.event=clockEvent;document.getElementById('liveLatencyTest').checked=true;return true;")
    outcome['clock_mutations_no_settings_save_echo']=True
    # Kısa gerçek timer: özel kullanıcı metni/boss yok; aynı Live ses/transkript hattı.
    js("testMicOff();const c=await import('./js/clocks.js');await c.createNativeClock('timer',1);return true;")
    wait_until(lambda:'Native personalized timer completion' in window.evaluate_js("document.getElementById('msgs').textContent") and not window.evaluate_js("document.getElementById('send').disabled"))
    assert 'Timer finished, boss.' not in window.evaluate_js("document.getElementById('msgs').textContent")
    assert 'Host event:' not in window.evaluate_js("document.getElementById('msgs').textContent")
    assert 'playback finished' in window.evaluate_js("document.getElementById('textStatus').textContent")
    outcome['timer_completed_via_scoped_live_audio_without_fake_user_bubble']=True



def check_native_shutdown_request(window, api, js, wait_until, outcome):
    """Model isteği/çalma/Stop sınırını gerçek DOM'da, host ret taklidiyle sına.

    Model ve core aracı gerçektir; sağlayıcı sentetiktir. Pencereyi testin
    ortasında kapatmamak için yalnız son shutdown olayı reddedilir. Gerçek
    worker/pencere kapanışı ayrı native shutdown senaryosunda doğrulanır.
    """
    js("window.shutdownErrors=[];window.addEventListener('unhandledrejection',e=>shutdownErrors.push(String(e.reason?.stack||e.reason)));window.shutdownModels=Array.from(document.getElementById('mSel').options).filter(o=>o.value).map(o=>({id:o.value,name:o.textContent}));window.shutdownModel=document.getElementById('mSel').value;window.shutdownCalls=0;window.shutdownEvent=window.pywebview.api.event;window.pywebview.api.event=(name,data)=>{if(name==='shutdown'){shutdownCalls++;return Promise.resolve({ok:false,error:'Synthetic host refusal'});}return shutdownEvent(name,data);};"
       "const a=await import('./js/live_audio.js');window.shutdownFinish=a.liveAudio.finish;a.liveAudio.finish=async function(id){const r=await shutdownFinish.call(this,id);window.shutdownPlaybackWaiting=true;await new Promise(resolve=>window.releaseShutdownPlayback=resolve);return r;};return true;")
    for mode in ('rest','live'):
        for guard in ('stop','connection','finish'):
            before = window.evaluate_js('window.shutdownCalls')
            prompt = 'Native SHUTDOWN '+mode+' '+guard
            js("window.shutdownPlaybackWaiting=false;document.getElementById('liveLatencyTest').checked="+str(mode=='live').lower()+";document.getElementById('inp').value="+json.dumps(prompt)+";document.getElementById('send').click();return true;")
            wait_until(lambda: window.evaluate_js('window.shutdownPlaybackWaiting'))
            assert window.evaluate_js('window.shutdownCalls') == before
            assert api._core._worker.is_alive()
            if guard == 'stop':
                js("document.getElementById('stopTask').click();return true;")
            elif guard == 'connection':
                js("window.dispatchEvent(new Event('taskvex-key-saved'));return true;")
            js('releaseShutdownPlayback();return true;')
            wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
            expected = before + (1 if guard == 'finish' else 0)
            wait_until(lambda: window.evaluate_js('window.shutdownCalls') == expected)
            if guard == 'finish':
                assert 'shutdown was not confirmed' in window.evaluate_js("document.getElementById('textStatus').textContent")
            outcome[mode+'_shutdown_'+guard+'_guard'] = True
    js("window.pywebview.api.event=shutdownEvent;const a=await import('./js/live_audio.js');a.liveAudio.finish=shutdownFinish;document.getElementById('liveLatencyTest').checked=true;const c=await import('./js/connections.js');c.setCatalog({models:shutdownModels,currentModel:shutdownModel});return true;")


def check_local_sleep(window, api, js, wait_until, live_state, wake_state, outcome):
    """Tek uyku kabul senaryosunu ayrı tut; native kontrol akışını büyütme."""
    # Komut yanıtı modeldendir; uyurken sıradan ses KWS hit'i olmadan
    # Live açmaz. Uyku geçişi gerçek oynatıcı bitişini beklemelidir.
    js("const a=await import('./js/live_audio.js');window.originalSleepFinish=a.liveAudio.finish;window.sleepPlaybackBlocked=false;"
       "a.liveAudio.finish=async function(id){const result=await originalSleepFinish.call(this,id);if(window.holdSleepPlayback){window.sleepPlaybackBlocked=true;await new Promise(r=>window.releaseSleepPlayback=r);}return result;};"
       "window.savedAudioContext=AudioContext;window.AudioContext=class extends savedAudioContext{constructor(o){super(o);if(o?.sampleRate===16000)window.capturedMicContext=this;}};"
       "window.wakeContext=new AudioContext();window.wakeOsc=wakeContext.createOscillator();window.wakeDestinations=[];wakeOsc.start();"
       "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{const d=wakeContext.createMediaStreamDestination();wakeDestinations.push(d);return d.stream;}});"
       "testMicOn();return true;")
    wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
    # Gerçek Web Audio suspend/ret yolları; fiziksel mikrofon veya API yok.
    before_recovery = live_state['opened']
    js("window.beforeResumeContext=capturedMicContext;await capturedMicContext.suspend();return true;")
    wait_until(lambda: js("return capturedMicContext.state==='running';"))
    assert js("const m=await import('./js/live_mic.js');return capturedMicContext===beforeResumeContext && m.liveMic.waitingForSpeech;")
    js("capturedMicContext.resume=()=>Promise.reject(new Error('Synthetic resume rejection'));await capturedMicContext.suspend();return true;")
    wait_until(lambda: 'audio engine did not resume' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    assert js("const m=await import('./js/live_mic.js');return !m.liveMic.active && document.getElementById('micB').classList.contains('on');")
    js("testMicOff();testMicOn();return true;")
    wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
    assert js("return capturedMicContext!==beforeResumeContext;")
    assert live_state['opened'] == before_recovery
    js("window.AudioContext=savedAudioContext;return true;")
    outcome['audio_context_suspend_resumed_same_source_or_explicit_on_recovered_without_api'] = True
    js("window.holdSleepPlayback=true;document.getElementById('inp').value='Lütfen, uyku moduna gir.';document.getElementById('send').click();return true;")
    wait_until(lambda: js("return sleepPlaybackBlocked;"))
    assert not api._sleeping
    assert 'Tamam efendim, geçiyorum.' in window.evaluate_js("document.getElementById('msgs').textContent")
    js("document.getElementById('stopTask').click();window.holdSleepPlayback=false;releaseSleepPlayback();return true;")
    wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
    assert not api._sleeping
    outcome['stop_during_sleep_reply_did_not_apply_sleep'] = True
    wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
    js("window.holdSleepPlayback=true;window.sleepPlaybackBlocked=false;document.getElementById('inp').value='Lütfen, uyku moduna gir.';document.getElementById('send').click();return true;")
    wait_until(lambda: js("return sleepPlaybackBlocked;"))
    assert not api._sleeping
    js("window.holdSleepPlayback=false;releaseSleepPlayback();return true;")
    wait_until(lambda: 'Asleep · say' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    outcome['sleep_waited_for_model_and_playback_drain'] = True
    assert window.evaluate_js("document.getElementById('sLbl').textContent") == 'SLEEPING'
    assert window.evaluate_js("!!document.getElementById('c_sleeping')")
    js("const c=document.getElementById('c_sleeping');c.value='#556677';c.dispatchEvent(new Event('input',{bubbles:true}));document.getElementById('btnSaveSet').click();return true;")
    wait_until(lambda: api._store.read().get('colors',{}).get('sleeping') == '#556677')
    assert window.evaluate_js("document.documentElement.style.getPropertyValue('--c')") == '#556677'
    outcome['sleeping_state_color_customization_persisted'] = True
    live_before_sleep = (live_state['opened'], len(live_state['sent']))
    local_before = wake_state['packets']
    js("wakeOsc.connect(wakeDestinations.at(-1));return true;")
    wait_until(lambda: wake_state['packets'] >= local_before + 5)
    assert js("return parseFloat(document.getElementById('nlv').style.width)>0;")
    outcome['real_worklet_microphone_meter_received_synthetic_audio']=True
    assert (live_state['opened'], len(live_state['sent'])) == live_before_sleep
    assert api._sleeping and not api._chat.busy
    js("testMicOff();return true;")
    wait_until(lambda: api._wake is None)
    assert window.evaluate_js("document.getElementById('nlv').style.width")=='0%'
    after_off = wake_state['packets']; time.sleep(.2)
    assert wake_state['packets'] == after_off
    js("testMicOn();return true;")
    wait_until(lambda: 'Asleep · say' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    wake_state['detect'] = True
    js("wakeOsc.connect(wakeDestinations.at(-1));return true;")
    wait_until(lambda: 'Native microphone answer' in window.evaluate_js("document.getElementById('msgs').textContent"))
    wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
    assert not api._sleeping
    assert window.evaluate_js("document.getElementById('sleep').textContent") == 'Sleep'
    js("const p=await import('./js/panels.js');p.openM('mProf');document.getElementById('pWake').value='Computer';document.getElementById('btnSaveProf').click();return true;")
    wait_until(lambda: api._store.read().get('prof',{}).get('pWake') == 'Computer')
    wake_state['detect'] = False
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: 'say "Computer"' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: not api._sleeping and window.evaluate_js("document.getElementById('sleep').textContent==='Sleep' && !document.getElementById('sleep').disabled"))
    js("testMicOff();wakeOsc.stop();await wakeContext.close();return true;")
    # Mikrofon kapalıyken de uyku backend'e ulaşmalı; yalnız UI etiketi değişmemeli.
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: api._sleeping and 'Asleep · Microphone Off' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    wait_until(lambda: api._wake is None)
    assert js("const m=await import('./js/live_mic.js');return !m.liveMic.active;")
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: not api._sleeping and window.evaluate_js("document.getElementById('sleep').textContent==='Sleep' && !document.getElementById('sleep').disabled"))
    outcome['sleep_with_microphone_off_closed_live_without_capture'] = True
    outcome['one_time_sleep_local_only_pcm_wake_handoff_mic_off_and_profile_word'] = True
    # Yerel motor hatası açık Wake'ten sonra normal konuşmayı kilitlememeli.
    from app.bridge import webview_bridge as bridge_module
    original_detector = bridge_module.WakeWord
    def unavailable(word, sensitivity=50):
        raise FileNotFoundError('Synthetic missing local model')
    bridge_module.WakeWord = unavailable
    js("testMicOn();return true;")
    wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: 'Local wake unavailable' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    assert api._sleeping
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
    assert not api._sleeping
    bridge_module.WakeWord = original_detector
    outcome['manual_wake_recovered_normal_listening_after_local_engine_failure'] = True
    js("testMicOff();return true;")
    check_wake_recovery(window, api, js, wait_until, live_state, outcome)
    # Gerçek host uyku reddi: UI bunu KWS eksikliği veya SLEEPING saymamalı.
    original_reset = api._chat.reset_live
    api._chat.reset_live = lambda **kwargs: False
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: 'Sleep was rejected' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    assert not api._sleeping
    assert window.evaluate_js("document.getElementById('sleep').textContent") == 'Sleep'
    assert window.evaluate_js("document.getElementById('sLbl').textContent") != 'SLEEPING'
    api._chat.reset_live = original_reset
    # IPC beklerken hazırlık görünür; kabul gelince gerçek uyku gösterilir.
    js("window.sleepOriginalEvent=window.pywebview.api.event;window.pywebview.api.event=async(n,d)=>{if(n==='sleep_start')await new Promise(r=>setTimeout(r,600));return sleepOriginalEvent(n,d);};document.getElementById('sleep').click();return true;")
    assert window.evaluate_js("document.getElementById('sleep').textContent") == 'Preparing sleep…'
    assert not api._sleeping
    wait_until(lambda: api._sleeping and 'Asleep · Microphone Off' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    js("window.pywebview.api.event=sleepOriginalEvent;document.getElementById('sleep').click();return true;")
    wait_until(lambda: not api._sleeping and window.evaluate_js("!document.getElementById('sleep').disabled"))
    outcome['sleep_host_rejection_and_pending_confirmation_not_fake_asleep'] = True
    # Kalıcı komut gerçek model yanıtından sonra uygulanır; Mic Off korunur.
    js("const d=document.getElementById('sleepDelay');d.value='2';d.dispatchEvent(new Event('change'));document.getElementById('btnSaveSet').click();return true;")
    wait_until(lambda: api._store.read().get('sleepDelay') == 2)
    opened = live_state['opened']
    js("document.getElementById('inp').value='Uyku moduna kalıcı olarak gir';document.getElementById('send').click();return true;")
    wait_until(lambda: api._sleeping and 'Asleep · Microphone Off' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: not api._sleeping and window.evaluate_js("!document.getElementById('send').disabled"))
    time.sleep(2.3)
    assert not api._sleeping  # Stay asleep timer'a değil, gerçek etkileşim bitişine bağlıdır.
    js("document.getElementById('inp').value='Live test';document.getElementById('send').click();return true;")
    wait_until(lambda: api._sleeping and 'Asleep · Microphone Off' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    assert live_state['opened'] == opened + 2
    # Kalıcı moddan çıkış, bağımsız normal boşta timer'ını kapatmaz.
    js("document.getElementById('inp').value='Disable persistent sleep mode';document.getElementById('send').click();return true;")
    wait_until(lambda: 'Tamam efendim, kalıcı uyku modunu kapatıyorum.' in window.evaluate_js("document.getElementById('msgs').textContent") and not window.evaluate_js("document.getElementById('send').disabled"))
    assert not api._sleeping
    wait_until(lambda: api._sleeping and 'Asleep · Microphone Off' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    assert live_state['opened'] == opened + 3
    # Bir kez uyandırılır; normal timer bu tercihi kalıcı moda dönüştürmemiştir.
    js("const d=document.getElementById('sleepDelay');d.value='0';d.dispatchEvent(new Event('change'));document.getElementById('sleep').click();return true;")
    wait_until(lambda: not api._sleeping)
    time.sleep(2.3)
    assert not api._sleeping
    assert not window.evaluate_js("document.getElementById('micB').classList.contains('on')")
    outcome['persistent_task_returns_immediately_and_normal_idle_timer_sleeps_once'] = True
    outcome['natural_sleep_enter_and_permanent_enter_reached_confirmed_host_modes'] = True
    # Native Mic yolu kamera ile aynı tek blip'i çağırmalı; fiziksel ses testi değildir.
    js("const s=await import('./js/sfx.js');window.originalBlip=s.sfx.blip;window.micBlips=0;s.sfx.blip=()=>{micBlips++;};testMicOn();testMicOff();s.sfx.blip=originalBlip;return true;")
    assert window.evaluate_js('window.micBlips') == 2
    outcome['native_microphone_on_off_each_called_camera_blip'] = True
    js("const a=await import('./js/live_audio.js');a.liveAudio.finish=originalSleepFinish;return true;")
    if os.environ.get('TASKVEX_TEST_REAL_WAKE') == '1':
        check_real_local_wake(window, api, js, wait_until, outcome)


def check_wake_recovery(window, api, js, wait_until, live_state, outcome):
    """Gerçek worklet kuyruğunu geciktir; yeniden hazırlama yeni komut değildir."""
    js("window.recoveryContext=new AudioContext();window.recoveryStream=null;"
       "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{recoveryStream=recoveryContext.createMediaStreamDestination().stream;return recoveryStream;}});"
       "window.recoveryOriginalEvent=window.pywebview.api.event;window.recoveryFeeds=0;window.recoveryDelayedDone=false;"
       "window.pywebview.api.event=async(name,data)=>{const delay=name==='wake_feed'&&++recoveryFeeds===1;"
       "if(delay)await new Promise(r=>setTimeout(r,1400));const value=await recoveryOriginalEvent(name,data);"
       "if(delay)recoveryDelayedDone=true;return value;};testMicOn();return true;")
    wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: 'Asleep · say' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    assert api._wake is not None
    original_id, opened = api._wake.id, live_state['opened']
    wait_until(lambda: 'Preparing fresh local wake' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    assert window.evaluate_js("document.getElementById('micB').classList.contains('on')")
    wait_until(lambda: api._wake is not None and api._wake.id != original_id and 'Asleep · say' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    wait_until(lambda: window.evaluate_js('window.recoveryDelayedDone'))
    assert api._sleeping and not api._chat.busy and live_state['opened'] == opened
    js("recoveryStream.getTracks()[0].dispatchEvent(new Event('ended'));return true;")
    wait_until(lambda: 'capture ended' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    assert 'capture ended' in window.evaluate_js("document.getElementById('textStatus').textContent")
    # Açık Wake ve ardından gerçek cihaz hatası → açık Sleep tekrar hazırlanır.
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
    js("recoveryStream.getTracks()[0].dispatchEvent(new Event('ended'));return true;")
    wait_until(lambda: 'capture ended' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    js("document.getElementById('sleep').click();return true;")
    wait_until(lambda: 'Asleep · say' in window.evaluate_js("document.getElementById('textStatus').textContent"))
    assert window.evaluate_js("document.getElementById('micB').classList.contains('on')")
    js("window.pywebview.api.event=recoveryOriginalEvent;document.getElementById('sleep').click();return true;")
    wait_until(lambda: not api._sleeping)
    js("testMicOff();await recoveryContext.close();return true;")
    outcome['local_wake_backpressure_recovered_without_live_and_preserved_on'] = True
    outcome['explicit_sleep_retried_blocked_device_with_reason'] = True


def check_real_local_wake(window, api, js, wait_until, outcome):
    """İsteğe bağlı yerel fixture: gerçek KWS + WebAudio; sağlayıcı hâlâ sentetik.

    Test önceden indirilmiş hash doğrulamalı modeli ve SAPI ile oluşturulmuş
    İngilizce WAV'ı kullanır. Ağ/gerçek mikrofon/kullanıcı sesi kullanılmaz.
    """
    from base64 import b64encode
    from app.bridge import webview_bridge as bridge_module
    from app.session import wake_word
    fixture = Path(__file__).resolve().parents[1] / 'runtime'
    original_home, original_detector = wake_word.model_home, bridge_module.WakeWord
    wake_word.model_home = lambda: fixture/'wake-model'
    bridge_module.WakeWord = wake_word.WakeWord
    try:
        encoded = b64encode((fixture/'wake-positive.wav').read_bytes()).decode('ascii')
        js("const p=await import('./js/panels.js');p.openM('mProf');document.getElementById('pWake').value='Vex';document.getElementById('btnSaveProf').click();return true;")
        wait_until(lambda: api._store.read().get('prof',{}).get('pWake') == 'Vex')
        js("window.realWakeContext=new AudioContext();window.realWakeDest=null;"
           "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{realWakeDest=realWakeContext.createMediaStreamDestination();return realWakeDest.stream;}});"
           "testMicOn();return true;")
        wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
        js("document.getElementById('sleep').click();return true;")
        wait_until(lambda: 'Asleep · say' in window.evaluate_js("document.getElementById('textStatus').textContent"))
        delay = int(os.environ.get('TASKVEX_WAKE_IDLE_SECONDS','0'))
        if delay not in (0,5,65):
            raise ValueError('Native wake delay must be 0, 5 or 65 seconds')
        for _ in range(delay):
            time.sleep(1)
        assert api._sleeping and api._wake is not None
        before_answers = window.evaluate_js("document.getElementById('msgs').textContent").count('Native microphone answer')
        js("const b=Uint8Array.from(atob(" + json.dumps(encoded) + "),c=>c.charCodeAt(0));const s=realWakeContext.createBufferSource();s.buffer=await realWakeContext.decodeAudioData(b.buffer);s.connect(realWakeDest);s.start();return true;")
        wait_until(lambda: not api._sleeping)
        # Backend hit'i, UI'nın yanıt turunu başlatıp bitirdiği anlamına gelmez.
        # Eski enabled düğmesini görüp capture'ı erken kapatma.
        wait_until(lambda: window.evaluate_js("document.getElementById('msgs').textContent").count('Native microphone answer') > before_answers)
        wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
        outcome['real_kws_sapi_wav_through_web_audio_and_native_bridge'] = True
        outcome[f'real_wake_after_{delay}_seconds_idle'] = True
        js("testMicOff();await realWakeContext.close();return true;")
    finally:
        wake_word.model_home, bridge_module.WakeWord = original_home, original_detector


def child(home: Path, phase: str, debug: bool = False) -> None:
    """Üretimdeki main() kurulumunu gerçek native motorla çalıştır."""
    os.environ["TASKVEX_HOME"] = str(home)
    faulthandler.dump_traceback_later(30)
    import webview
    # Açık kullanıcı uygulamasının 42001 sunucusuna bağlanma. Aynı test
    # profilinin yeniden açılışlarında origin yine sabit kalmalıdır.
    home.mkdir(parents=True, exist_ok=True)
    port_file = home / 'test-http-port'
    if not port_file.exists():
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port_file.write_text(str(listener.getsockname()[1]), encoding='ascii')
    webview.settings['DEFAULT_HTTP_PORT'] = int(port_file.read_text(encoding='ascii'))
    from app.main import main
    from app.storage.json_store import StoreError

    captured, outcome, launches = {}, {}, []
    key_query_started, release_key_query = Event(), Event()
    original_create, original_start = webview.create_window, webview.start
    text_started, release_text = Event(), Event()
    rest_stop_started, release_rest_stop = Event(), Event()
    text_requests = []
    wake_state = {'packets':0, 'detect':False, 'instances':0}
    speech_state = {'requests': [], 'fail': False, 'block': False, 'started': Event(), 'release': Event()}
    text_payloads = []  # Yalnız geçici test profilinin SDK talimatını denetler.
    if phase != 'chat':
        # Otomatik katalog yeni açılış davranışıdır; gerçek hesap/ağ kullanma.
        from app.bridge import webview_bridge as catalog_bridge
        catalog_bridge.load_live_catalog = lambda: {'ok':True,'completed':True,'models':[]}
    catalog_ready = Event()
    live_state: dict = {"opened": 0, "closed": False, "sent": [], "waiting": Event(), "stall": False,
                        "resumed": False}
    if phase == "chat":
        # Gerçek SDK/core/native DOM; yalnız HTTP taşıması sentetiktir.
        # Üretim anahtarı okunmaz ve dış ağa istek çıkmaz.
        import httpx
        from app.bridge import webview_bridge as bridge_module
        class SyntheticWake:
            """Yalnız algılama sınırı sahte; gerçek PCM/bridge/Live devri denenir."""
            def __init__(self, word, sensitivity=50):
                wake_state['instances'] += 1
                self.id = 'native-local-wake-' + str(wake_state['instances'])
                self.sequence = 0
            def feed(self, sequence, pcm):
                assert sequence == self.sequence and len(pcm) == 3200
                self.sequence += 1
                wake_state['packets'] += 1
                return wake_state['detect'] and any(pcm)
        bridge_module.WakeWord = SyntheticWake
        from app.session import gemini
        from contextlib import asynccontextmanager
        from google.genai import live

        def audio_reply(text, samples=2400):
            """Gerçek Web Audio'ya sessiz PCM ver; fiziksel ses kabulü iddia etme."""
            from base64 import b64encode
            return {"serverContent": {"modelTurn": {"role": "model", "parts": [{"inlineData": {
                "data": b64encode(b'\x00\x00' * samples).decode(), "mimeType": "audio/pcm;rate=24000"}}]},
                "outputTranscription": {"text": text}, "turnComplete": True}}

        def crud_plan(text):
            """Yalnız sentetik kullanıcı komutundan gerçek depodaki ID'yi seç.

            Model taklidi yalnız taşıma sınırındadır; kayıt değişikliği yapmaz.
            Liste/işlem/son yanıt üretim ModelTools ve TaskManager'dan geçer.
            """
            from app.storage.json_store import JsonStore
            from app.tools.local.notes import notes_snapshot
            if text.startswith('Native BULK '):
                data = JsonStore(home / 'notes.json').read()
                assert data is not None
                saved = data['notes']
                latest = text in ('Native BULK latest', 'Native BULK latest_done')
                selected = sorted(saved, key=lambda n:n.get('created_at') or '', reverse=True)[:2] if latest else saved
                return [('notes.select', {'kind':'latest','count':2,'cardinality':'many'} if latest else
                    {'kind':'all','cardinality':'many'}), ('notes.complete_many' if text.endswith(('_done','_reopen')) else 'notes.delete_many', {
                        'ids':[n['id'] for n in selected], 'expected_snapshot':notes_snapshot(saved),
                        **({'done':not text.endswith('_reopen')} if text.endswith(('_done','_reopen')) else {})})]
            verb, target = text.removeprefix("Native CRUD ").split(": ", 1)
            target = target.split(" | ", 1)[0]
            snapshot = JsonStore(home / "notes.json").read()
            assert snapshot is not None
            saved = snapshot["notes"]
            matches = [note for note in saved if note["text"] == target]
            assert len(matches) == 1
            args = {"id": matches[0]["id"], "expected_snapshot": notes_snapshot(saved)}
            if verb == "done":
                args["done"] = True
            elif verb == "edit":
                args["text"] = target + " edited"
            selector = ({'kind':'contains','text':'synthetic','cardinality':'one'} if verb == 'done'
                else {'kind':'latest','count':1,'cardinality':'one'})
            return [('notes.select', selector), ('notes.delete' if verb == 'delete' else 'notes.update', args)]

        def clock_plan(text):
            """Yalnız sentetik sağlayıcı fixture'ı; üretim doğal dil parser'ı değildir."""
            _, _, mode, action = text.split()
            if action in ('watch', 'timer1', 'timer2'):
                args={'kind':'stopwatch' if action=='watch' else 'timer', 'start':True, 'label':mode+' '+action}
                if action!='watch':args['duration_seconds']=120 if action=='timer1' else 180
                return [('clocks.create',args)]
            target='timer1' if action=='pause_timer1' else 'watch'
            clock=next(c for c in captured['api']._clocks.snapshot()['clocks'] if c['label']==mode+' '+target)
            return [('clocks.list',{}),('clocks.control',{'id':clock['id'],'action':'pause' if action=='pause_timer1' else 'reset'})]

        @asynccontextmanager
        async def live_socket(*args, **kwargs):
            live_state["opened"] += 1
            live_state.update(closed=False, stall=False)
            frames = [{"setupComplete": {}}]
            turns = 0
            remembered_name = None
            class Socket:
                async def send(self, value):
                    nonlocal turns, remembered_name
                    message = json.loads(value)
                    live_state["sent"].append(message)
                    if 'client_content' in message:
                        assert message['client_content']['turnComplete'] is False
                        for turn in message['client_content']['turns']:
                            assert turn['role'] == 'model'
                            for part in turn['parts']:
                                history = json.loads(part['text'].split('Historical JSON:\n', 1)[1])
                                if any(row['user'] == 'Native temporary name is Ada' for row in history):
                                    remembered_name = 'Ada'
                        return
                    if 'setup' in message:
                        self.setup_tools=message['setup'].get('tools',[])
                    if "setup" in message and live_state["opened"] == 2:
                        assert message["setup"]["sessionResumption"]["handle"] == "NATIVE_SYNTHETIC_RESUME_HANDLE"
                        live_state["resumed"] = True
                    if "realtime_input" in message:
                        incoming = message['realtime_input']
                        if incoming.get('audioStreamEnd'):
                            raise AssertionError('Manual VAD must use activityEnd, not audioStreamEnd')
                        if 'activityEnd' in incoming:
                            live_state['input_ended'] = live_state.get('input_ended', 0) + 1
                            if live_state.get('hold_microphone_reply'):
                                # Thinking görünümünü kısa bir zaman aralığını
                                # şansla yakalamaya değil açık test bariyerine bağla.
                                while live_state.get('hold_status_reply'):
                                    import asyncio
                                    await asyncio.sleep(.001)
                                frames.append(audio_reply('Native microphone Off answer'))
                            elif not getattr(self, 'media_answered', False):
                                frames.append({'serverContent':{'inputTranscription':{'text':'Native microphone hello'}}})
                                frames.append(audio_reply('Native microphone answer'))
                            self.media_answered = True
                            return
                        if 'audio' in incoming:
                            # SDK'nin wire biçimi URL-safe base64'dür;
                            # standart decoder '-'/'_' örneklerini bozabilir.
                            from base64 import urlsafe_b64decode
                            if live_state.get('hold_microphone_reply'):
                                if any(urlsafe_b64decode(incoming['audio']['data'])):
                                    live_state['voice_seen'] = True
                                    live_state['quiet_packets'] = 0
                                elif live_state.get('voice_seen'):
                                    live_state['quiet_packets'] = live_state.get('quiet_packets', 0) + 1
                                    if live_state['quiet_packets'] == 15:
                                        frames.append(audio_reply('Native status reply', 12000))
                                return
                            if any(urlsafe_b64decode(incoming['audio']['data'])) and not getattr(self, 'media_answered', False):
                                frames.append({'serverContent':{'inputTranscription':{'text':'Native microphone hello'}}})
                                frames.append(audio_reply('Native microphone answer'))
                                self.media_answered = True
                            return
                        if 'activityStart' in incoming:
                            self.media_answered = False
                            return
                        text = message["realtime_input"].get("text", "")
                        # Yalnız sentetik sağlayıcının önceden belirlenmiş araç
                        # seçimi; üretimde cümle kalıbı veya niyet parser'ı yok.
                        if text.startswith('Host event: the following timer has actually finished.'):
                            assert not self.setup_tools
                            live_state['timer_announcements']=live_state.get('timer_announcements',0)+1
                            frames.append(audio_reply('Native personalized timer completion'))
                            return
                        if text.startswith('Native CLOCK '):
                            frames.extend({'toolCall':{'functionCalls':[{'id':'clock-'+text+'-'+str(i),'name':name,'args':args}]}}
                                for i,(name,args) in enumerate(clock_plan(text)))
                            frames.append({'serverContent':{'outputTranscription':{'text':text+' confirmed'},'turnComplete':True}})
                            return
                        if text.startswith('Native SHUTDOWN '):
                            live_state['shutdown_calls'] = live_state.get('shutdown_calls', 0) + 1
                            frames.append({'toolCall': {'functionCalls': [{'id': 'shutdown-'+str(live_state['shutdown_calls']),
                                'name': 'assistant.request_shutdown', 'args': {}}]}})
                            return
                        mode = {'Lütfen, uyku moduna gir.': 'once',
                            'Uyku moduna kalıcı olarak gir': 'persistent',
                            'Disable persistent sleep mode': 'off'}.get(text)
                        if mode:
                            live_state['sleep_requests'] = live_state.get('sleep_requests', 0) + 1
                            frames.append({'toolCall': {'functionCalls': [{'id': 'native-sleep-' + str(live_state['sleep_requests']),
                                'name': 'assistant.request_sleep_mode', 'args': {'mode': mode}}]}})
                            return
                        if text == 'Native server interruption':
                            frames.append({'serverContent':{'outputTranscription':{'text':'Native interrupted reply'}, 'interrupted':True}})
                            return
                        if text == 'Native temporary name is Ada':
                            remembered_name = 'Ada'
                            frames.append(audio_reply('Native temporary name acknowledged'))
                            return
                        if text == 'Native memory ask':
                            frames.append(audio_reply('Native remembered name: ' + (remembered_name or 'unknown')))
                            return
                        if text == 'Native profile probe':
                            frames.append(audio_reply('Native profile probe Live'))
                            return
                        if text == 'Native microphone rejected note':
                            # Var olmayan hedef reddedilmeli; kayıt/izin hattı
                            # üretim kodudur. Model hatası mikrofonu Off yapmaz.
                            frames.append({'toolCall':{'functionCalls':[{'id':'missing-note-call','name':'notes.delete',
                                'args':{'id':'missing-synthetic-note'}}]}})
                            return
                        if text == 'Native barge active':
                            frames.append({'toolCall':{'functionCalls':[{'id':'native-barge-note','name':'notes.add',
                                'args':{'text':'Committed before barge-in'}}]}})
                            return
                        if text == 'Native barge playback':
                            frames.append(audio_reply('Native barge playback reply', 60000))
                            return
                        if text == 'Native barge waiting':
                            reply = audio_reply('Native barge waiting reply', 60000)
                            reply['serverContent']['turnComplete'] = False
                            frames.append(reply)
                            live_state['stall'] = True
                            return
                        if text in {"Native playback only", "Native audio muted", "Native key switch"}:
                            frames.append(audio_reply(text + " reply", 2400 if text == "Native audio muted" else 48000))
                            return
                        if text.startswith(("Native CRUD ", "Native BULK ")):
                            for index, (name, arguments) in enumerate(crud_plan(text)):
                                frames.append({"toolCall": {"functionCalls": [{"id": f"native-crud-{text}-{index}",
                                    "name": name, "args": arguments}]}})
                            frames.append({"serverContent": {"outputTranscription": {
                                "text": text + " confirmed"}, "turnComplete": True}})
                            return
                        if message["realtime_input"].get("text") == "Native Stop":
                            live_state["stall"] = True
                            return
                        turns += 1
                        if turns >= 3:
                            # Üçüncü ve dördüncü tur aynı çağrı kimliğini yollar:
                            # gerçek core tek not yazmalı, UI her sonucu yenilemeli.
                            frames.append({"toolCall": {"functionCalls": [{"id": "live-ui-note",
                                "name": "notes.add", "args": {"text": "Live UI synthetic note"}}]}})
                        else:
                            frames.append(audio_reply("Live synthetic reply" if turns == 1 else "Live reused reply"))
                    elif "tool_response" in message:
                        response = message["tool_response"]["functionResponses"][0]
                        assert response["response"]["result"]["verified"]
                        if response['id'].startswith('clock-Native CLOCK '):return
                        if response['name'] == 'assistant.request_shutdown':
                            assert response['response']['result']['data']['applied'] is False
                            frames.append(audio_reply('TaskVex kapanacak.', 12000))
                            return
                        if response['name'] == 'assistant.request_sleep_mode':
                            data = response['response']['result']['data']
                            assert data['applied'] is False
                            frames.append(audio_reply('Tamam efendim, kalıcı uyku modunu kapatıyorum.' if data['mode'] == 'off'
                                else 'Tamam efendim, geçiyorum.', 12000))
                            return
                        if response["id"].startswith("native-crud-"):
                            return
                        if response['id'] == 'native-barge-note':
                            reply = audio_reply('Native barge active reply', 60000)
                            reply['serverContent']['turnComplete'] = False
                            frames.append(reply)
                            live_state['stall'] = True
                            return
                        frames.append(audio_reply(f"Live tool saved turn {turns}"))
                        if turns == 4 and live_state["opened"] == 1:
                            # Biten turun güvenli checkpoint'i ve GoAway idle
                            # kuyruğuna düşer; sonraki metin eski socket'e gitmez.
                            frames.extend([{"sessionResumptionUpdate": {"resumable": True,
                                "newHandle": "NATIVE_SYNTHETIC_RESUME_HANDLE"}}, {"goAway": {"timeLeft": "10s"}}])
                async def recv(self, **kwargs):
                    if frames and 'setupComplete' in frames[0] and live_state.get('hold_setup'):
                        import asyncio
                        live_state['setup_waiting'] = True
                        while live_state.get('hold_setup'):
                            await asyncio.sleep(.001)
                    while not frames and not live_state["stall"]:
                        import asyncio
                        await asyncio.sleep(.001)  # Akış göndericisinin eklediği yanıtı da uyandır.
                    if not frames and live_state["stall"]:
                        import asyncio
                        live_state["waiting"].set()
                        await asyncio.sleep(3600)  # Stop gerçek SDK await'ini kesmeli.
                    return json.dumps(frames.pop(0)).encode()
            try:
                yield Socket()
            finally:
                live_state["closed"] = True
        setattr(live, "ws_connect", live_socket)
        os.environ["GEMINI_API_KEY"] = "TASKVEX_SYNTHETIC_KEY"
        original_client = gemini.genai.Client
        responses = [
            httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                "role": "model", "parts": [{"text": "Hello before notes confirmation"}]}}]}),
            httpx.Response(503, json={"error": {"code": 503}}),
            httpx.Response(503, json={"error": {"code": 503}}),
            httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                "role": "model", "parts": [{"functionCall": {"id": "native-note", "name": "notes.add",
                "args": {"text": "Chat synthetic note"}}, "thoughtSignature": "c2ln"}]}}]}),
            httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                "role": "model", "parts": [{"text": "Saved <img src=x onerror=alert(1)>"}]}}]}),
            httpx.Response(400, json={"error": {"code": 400, "message": "SECRET"}}),
        ]

        def handle_text(request):
            if request.url.path.endswith('/interactions'):
                from base64 import b64encode
                speech_state['requests'].append(json.loads(request.content))
                if speech_state['block']:
                    speech_state['started'].set()
                    assert speech_state['release'].wait(10)
                if speech_state['fail']:
                    return httpx.Response(503, json={'error':{'message':'SECRET'}})
                return httpx.Response(200, json={'id':'native-tts', 'status':'completed', 'steps':[
                    {'type':'model_output', 'content':[{'type':'audio', 'mime_type':'audio/l16',
                     'sample_rate':24000, 'data':b64encode(bytes(4800)).decode()}]}]})
            if request.method == "GET":
                assert catalog_ready.wait(10), "Synthetic capture was not installed before catalog loading"
                return httpx.Response(200, json={"models": [
                    {"name": "models/text-only", "supportedGenerationMethods": ["generateContent"]},
                    {"name": "models/future-live", "displayName": "Future Live", "supportedGenerationMethods": ["bidiGenerateContent"]},
                ]})
            text_requests.append(str(request.url))
            body = json.loads(request.content)
            text_payloads.append(body)
            prompt = body["contents"][0]["parts"][0].get("text", "")
            if prompt.startswith('Native CLOCK '):
                plan=clock_plan(prompt); index=(len(body['contents'])-1)//2
                parts=([{'functionCall':{'id':'clock-'+str(index),'name':plan[index][0],'args':plan[index][1]}}]
                    if index<len(plan) else [{'text':prompt+' confirmed'}])
                return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'role':'model','parts':parts}}]})
            if prompt.startswith('Native SHUTDOWN '):
                parts = ([{'functionCall': {'id':'shutdown-rest','name':'assistant.request_shutdown','args':{}}}]
                    if len(body['contents']) == 1 else [{'text':'TaskVex kapanacak.'}])
                return httpx.Response(200, json={'candidates': [{'finishReason':'STOP','content':{'role':'model','parts':parts}}]})
            if prompt == 'Native profile probe':
                return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {
                    'role': 'model', 'parts': [{'text': 'Native profile probe REST'}]}}]})
            if prompt.startswith(("Native CRUD ", "Native BULK ")):
                round_index = (len(body["contents"]) - 1) // 2
                if round_index == 2:
                    parts = [{"text": prompt + " confirmed"}]
                else:
                    # Sonraki HTTP turunda mutasyon zaten yapılmış olabilir;
                    # planı yalnız liste ve mutasyon yanıtı üretirken çözeriz.
                    name, arguments = crud_plan(prompt)[round_index]
                    parts = [{"functionCall": {"id": f"native-crud-{round_index}", "name": name, "args": arguments}}]
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                    "role": "model", "parts": parts}}]})
            if body["contents"][0]["parts"][0].get("text") == "Native REST Stop":
                rest_stop_started.set()
                assert release_rest_stop.wait(15)
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {
                    "role": "model", "parts": [{"functionCall": {"id": "must-not-run", "name": "notes.add",
                        "args": {"text": "Must not be saved after REST Stop"}}}]}}]})
            if len(text_requests) == 1:
                body = json.loads(request.content)
                assert {item["name"] for item in body["tools"][0]["functionDeclarations"]} == {"apps.catalog", "system.status", "assistant.request_sleep_mode", "assistant.request_shutdown", "clocks.create", "clocks.control", "clocks.list"}
                text_started.set()
                assert release_text.wait(20)
            assert responses, "Unexpected model retry"
            return responses.pop(0)

        def client(**kwargs):
            kwargs["http_options"].client_args = {"transport": httpx.MockTransport(handle_text)}
            return original_client(**kwargs)

        gemini.genai.Client = client
        gemini.GeminiText._wait_retry = lambda self, seconds: None

    def create(*args, **kwargs):
        kwargs["hidden"] = True
        captured["api"] = kwargs["js_api"]
        if phase == "credentials":
            original_event = captured["api"].event
            queries = []

            def event(name, data=None):
                result = original_event(name, data)
                if name == "query_apikey" and not queries:
                    queries.append(True)
                    key_query_started.set()
                    assert release_key_query.wait(25)
                return result

            captured["api"].event = event
        captured["window"] = original_create(*args, **kwargs)
        return captured["window"]

    def wait_until(check):
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            if check():
                return
            time.sleep(0.1)
        raise TimeoutError("Native acceptance condition was not reached")

    def exercise():
        window, api = captured["window"], captured["api"]

        def js(body):
            completed, result = Event(), {}

            def callback(value):
                result["value"] = value
                completed.set()

            window.evaluate_js("Promise.resolve().then(async()=>{" + body +
                               "}).catch(e=>({test_error:String(e)}))", callback=callback)
            assert completed.wait(15), "JS promise did not complete"
            value = result["value"]
            assert not (isinstance(value, dict) and "test_error" in value), value
            return value

        def export_backup(accept):
            """Dosya seçimini taklit et; gerçek WebView2 download yazımını dene."""
            from webview.platforms import edgechromium
            original_forms = getattr(edgechromium, "WinForms")
            export_path = home / ("exported-backup.json" if accept else "cancelled-backup.json")
            calls = []

            class SaveDialog:
                def ShowDialog(self, owner):
                    calls.append(True)
                    self.FileName = str(export_path)
                    return original_forms.DialogResult.OK if accept else original_forms.DialogResult.Cancel

            class FormsProxy:
                SaveFileDialog = SaveDialog

                def __getattr__(self, name):
                    return getattr(original_forms, name)

            setattr(edgechromium, "WinForms", FormsProxy())
            try:
                js("document.getElementById('expB').click();return true;")
                wait_until(lambda: len(calls) == 1)
                if accept:
                    wait_until(lambda: export_path.is_file() and export_path.stat().st_size > 0)
                    return json.loads(export_path.read_text('utf-8'))
                assert not export_path.exists()
                return None
            finally:
                setattr(edgechromium, "WinForms", original_forms)

        try:
            if phase in {"corrupt", "schema_invalid", "future"}:
                original = (home / "settings.json").read_bytes()
                existing_backups = set(home.glob("settings.json.*.corrupt"))
                wait_until(lambda: window.evaluate_js(
                    "typeof window.vex==='object' && document.getElementById('nativeIssue')?.hidden===false"))
                assert not api._ready
                assert "Native local note" in js("const s=await import('./js/settings.js');return JSON.stringify(s.store.notes);")
                if phase == "future":
                    assert window.evaluate_js("document.getElementById('recoverSettings').hidden")
                    assert "version" in window.evaluate_js("document.getElementById('nativeIssueText').textContent")
                    assert (home / "settings.json").read_bytes() == original
                    assert set(home.glob("settings.json.*.corrupt")) == existing_backups
                    outcome.update(ok=True, phase=phase, future_version_preserved=True, repair_hidden=True)
                    return
                assert not window.evaluate_js("document.getElementById('recoverSettings').hidden")
                retry = js("return await window.pywebview.api.event('retry_startup');")
                assert retry["ok"] is False and (home / "settings.json").read_bytes() == original
                js("window.confirm=()=>false;document.getElementById('recoverSettings').click();return true;")
                assert (home / "settings.json").read_bytes() == original
                assert set(home.glob("settings.json.*.corrupt")) == existing_backups
                before = js("const s=await import('./js/settings.js');return JSON.stringify([s.store.notes,s.store.skills,s.store.routines,s.store.prof]);")
                js("window.confirm=()=>true;document.getElementById('recoverSettings').click();return true;")
                wait_until(lambda: api._ready)
                wait_until(lambda: window.evaluate_js("document.getElementById('nativeIssue').hidden"))
                wait_until(lambda: api._notes_ready)
                wait_until(lambda: not window.evaluate_js("document.getElementById('noteAdd').disabled"))
                after = js("const s=await import('./js/settings.js');return JSON.stringify([s.store.notes,s.store.skills,s.store.routines,s.store.prof]);")
                assert after == before
                new_backups = set(home.glob("settings.json.*.corrupt")) - existing_backups
                assert len(new_backups) == 1 and new_backups.pop().read_bytes() == original
                assert api._store.read()["vol"] == 0.8
                if phase == "schema_invalid":
                    assert api._store.read()["prof"] == {"pIns": "Native profile 📝"}
                    assert api._store.read()["theme"] == "#4fd8ff"
                outcome.update(ok=True, phase=phase, issue_visible=True, declined_repair_preserved=True,
                               original_backed_up=True, repair_completed=True, local_data_preserved=True)
                return
            wait_until(lambda: api._ready)
            initial = js("return {alias:window.vex===window.jarvis, api:Object.keys(window.pywebview.api),"
                         "online:document.getElementById('netP').textContent,"
                         "system:document.getElementById('win').textContent};")
            assert initial["alias"] and initial["api"] == ["event"], initial
            assert "OFFLINE" in initial["online"] and initial["system"] != "—", initial
            if phase == "chat":
                # Yeni otomatik başlangıç fiziksel mikrofona hiç ulaşmasın.
                # Her izin çağrısı taze, sessiz bir sentetik track alır.
                js("window.defaultMicContext=new AudioContext();window.defaultMicTracks=[];"
                   "window.testMicOff=()=>{const b=document.getElementById('micB');if(b.getAttribute('aria-pressed')==='true')b.click();};"
                   "window.testMicOn=()=>{testMicOff();document.getElementById('micB').click();};"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=defaultMicContext.createMediaStreamDestination();defaultMicTracks.push(...d.stream.getTracks());return d.stream;}});return true;")
                js("const d=document.getElementById('sleepDelay');d.value='0';d.dispatchEvent(new Event('change'));return true;")
                wait_until(lambda: (api._store.read() or {}).get('sleepDelay') == 0)
                wait_until(lambda: window.evaluate_js("document.getElementById('dIn').options.length>0 && document.getElementById('dOut').options.length>0"))
                assert window.evaluate_js("document.getElementById('devB')===null")
                outcome['audio_devices_listed_at_startup_without_scan_button'] = True
                assert js("const input=document.getElementById('sleepDelay');document.getElementById('sleepMore').click();if(input.value!=='1')return false;document.getElementById('sleepLess').click();document.getElementById('sleepLess').click();if(input.value!=='0')return false;input.value='300';document.getElementById('sleepMore').click();if(input.value!=='300')return false;input.value='0';input.dispatchEvent(new Event('change'));return true;")
                outcome['themed_sleep_stepper_bounded_to_0_300']=True
                catalog_ready.set()
                assert window.evaluate_js("document.getElementById('refreshModels')===null")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                silent_requests = len(live_state['sent'])
                time.sleep(.3)
                assert len(live_state['sent']) == silent_requests
                assert not window.evaluate_js("document.getElementById('inp').disabled")
                outcome['automatic_listening_after_catalog_without_click_or_idle_api'] = True
                js("testMicOff();return true;")
                js("document.getElementById('liveLatencyTest').checked=false;return true;")
                wait_until(lambda: "Use backend notes" in window.evaluate_js("document.getElementById('notesConnect').textContent"))
                assert not api._notes_ready
                js("document.getElementById('inp').value='Hello before notes confirmation';"
                   "document.getElementById('send').click();return true;")
                assert text_started.wait(5)
                assert api._chat.busy
                assert window.evaluate_js("document.getElementById('send').disabled && document.getElementById('noteAdd').disabled")
                assert not api.event("text", "Duplicate")["ok"]
                assert not api.event("shutdown")["ok"]
                assert not api._chat.close()
                assert api.event("save", {"vol": 0.5})["ok"]
                release_text.set()
                wait_until(lambda: "Answered by" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert not api._notes_ready and "Hello before notes confirmation" in window.evaluate_js("document.getElementById('msgs').textContent")
                js("window.confirm=()=>true;document.getElementById('notesConnect').click();return true;")
                wait_until(lambda: api._notes_ready)
                js("document.getElementById('inp').value='Add the synthetic note';document.getElementById('send').click();return true;")
                wait_until(lambda: "gemini-3.5-flash-lite" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                state = js("return {notes:document.getElementById('notes').textContent,"
                           "answer:document.getElementById('msgs').textContent,"
                           "safe:!document.querySelector('#msgs img'),input:document.getElementById('inp').value,"
                           "online:document.getElementById('netP').textContent};")
                assert "Chat synthetic note" in state["notes"] and "Saved <img" in state["answer"]
                assert state["safe"] and state["input"] == "" and "gemini-3.5-flash-lite" in state["online"]
                assert len(text_requests) == 5 and "gemini-3.5-flash-lite" in text_requests[-1]
                assert 'playback finished' in window.evaluate_js("document.getElementById('textStatus').textContent")
                from app.core.contracts import ToolRequest
                from uuid import uuid4
                task = api._core.submit(ToolRequest(request_id=uuid4().hex, source="desktop",
                    principal="local-user", tool="notes.list"))
                finished = api._core.wait(task.task_id, timeout=3)
                assert finished.result is not None
                assert sum(n["text"] == "Chat synthetic note" for n in finished.result.data["notes"]) == 1
                document = (home / "notes.json").read_bytes()
                js("document.getElementById('inp').value='Rejected request';document.getElementById('send').click();return true;")
                wait_until(lambda: "HTTP 400" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert "invalid_request" in window.evaluate_js("document.getElementById('textStatus').textContent")
                assert "Model request:" in window.evaluate_js("document.getElementById('log').textContent")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert window.evaluate_js("document.getElementById('inp').value") == "Rejected request"
                assert "FAILED" in window.evaluate_js("document.getElementById('netP').textContent")
                assert "SECRET" not in window.evaluate_js("document.getElementById('log').textContent")
                assert (home / "notes.json").read_bytes() == document
                assert len(speech_state['requests']) == 2
                assert speech_state['requests'][-1]['input'][0]['content'][0]['text'] == 'Saved <img src=x onerror=alert(1)>'
                assert 'tools' not in speech_state['requests'][-1]
                # Ses hatası metni korur; Mute yeni TTS isteğini başlatmaz.
                speech_state['fail'] = True
                js("document.getElementById('inp').value='Native profile probe';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'audio unavailable: speech_unavailable' in window.evaluate_js("document.getElementById('textStatus').textContent")
                assert len(speech_state['requests']) == 3  # 503 TTS tekrarına dönüşmez.
                assert 'Native profile probe REST' in window.evaluate_js("document.getElementById('msgs').textContent")
                speech_state['fail'] = False
                speech_count = len(speech_state['requests'])
                js("document.getElementById('mute').click();document.getElementById('inp').value='Native profile probe';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert len(speech_state['requests']) == speech_count
                assert 'playback muted' in window.evaluate_js("document.getElementById('textStatus').textContent")
                js("document.getElementById('mute').click();return true;")
                # Metin görünürken sentez HTTP'si bekleyebilir. Stop kabulü,
                # gerçek HTTP bitmeden kontrolleri açmaz; kayıt geri alınmaz.
                speech_state['block'] = True
                js("document.getElementById('inp').value='Native profile probe';document.getElementById('send').click();return true;")
                assert speech_state['started'].wait(5)
                assert 'Native profile probe REST' in window.evaluate_js("document.getElementById('msgs').textContent")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: 'Speech stop requested' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js("document.getElementById('send').disabled") and api._chat.busy
                speech_state['release'].set()
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                speech_state['block'] = False
                assert (home / 'notes.json').read_bytes() == document
                outcome['rest_speech_text_first_failure_preserved_no_retry_mute_and_stop'] = True
                before_rest_stop = len(text_requests)
                js("document.getElementById('inp').value='Native REST Stop';document.getElementById('send').click();return true;")
                assert rest_stop_started.wait(5)
                assert not window.evaluate_js("document.getElementById('stopTask').disabled")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: "Waiting for the current HTTP request" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert api._chat.busy and window.evaluate_js("document.getElementById('send').disabled && document.getElementById('noteAdd').disabled")
                release_rest_stop.set()
                wait_until(lambda: "Stopped. Completed actions" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert (home / "notes.json").read_bytes() == document
                assert len(text_requests) == before_rest_stop + 1 and not api._chat.busy
                check_native_note_crud(home, window, js, wait_until, outcome, "rest", "Chat synthetic note")
                document = (home / "notes.json").read_bytes()
                assert window.evaluate_js("document.getElementById('mSel').value") == 'future-live'
                wait_until(lambda: "API Live models loaded" in window.evaluate_js("document.getElementById('liveCatalogStatus').textContent"))
                assert window.evaluate_js("Array.from(document.getElementById('mSel').options).map(o=>o.value)") == ['future-live']
                js("const select=document.getElementById('mSel');select.value='future-live';"
                   "select.dispatchEvent(new Event('change'));return true;")
                wait_until(lambda: api._live_model == 'future-live')
                wait_until(lambda: "Live model selected" in window.evaluate_js("document.getElementById('liveCatalogStatus').textContent"))
                assert api._model == 'gemini-3.8-flash'
                rest_requests = len(text_requests)
                js("window.nativeAudioPackets=[];const original=window.vex.audioChunk;"
                   "window.vex.audioChunk=packet=>{const accepted=original(packet);"
                   "window.nativeAudioPackets.push({id:packet.request_id,accepted});return accepted;};return true;")
                js("document.getElementById('liveLatencyTest').checked=true;document.getElementById('inp').value='Live test';"
                   "document.getElementById('send').click();return true;")
                wait_until(lambda: "first text" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert "Live synthetic reply" in window.evaluate_js("document.getElementById('msgs').textContent")
                assert "LAST LIVE TEST" in window.evaluate_js("document.getElementById('netP').textContent")
                assert live_state["opened"] == 1 and not live_state["closed"] and len(text_requests) == rest_requests
                js("document.getElementById('inp').value='Second Live message';document.getElementById('send').click();return true;")
                wait_until(lambda: "session reused" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert "Live reused reply" in window.evaluate_js("document.getElementById('msgs').textContent")
                assert live_state["opened"] == 1 and len(text_requests) == rest_requests
                assert (home / "notes.json").read_bytes() == document
                for turn in [3, 4]:
                    js("document.getElementById('inp').value='Live add note';document.getElementById('send').click();return true;")
                    wait_until(lambda: f"Live tool saved turn {turn}" in window.evaluate_js("document.getElementById('msgs').textContent"))
                    wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                    assert "Live UI synthetic note" in window.evaluate_js("document.getElementById('notes').textContent")
                from app.storage.json_store import JsonStore
                snapshot = JsonStore(home / "notes.json").read()
                assert snapshot is not None
                saved = snapshot["notes"]
                assert sum(note["text"] == "Live UI synthetic note" for note in saved) == 1
                assert live_state["opened"] == 1 and len(text_requests) == rest_requests
                before_stop = (home / "notes.json").read_bytes()
                logical_id = api._chat._live._connection.logical_id
                js("document.getElementById('inp').value='Resume check';document.getElementById('send').click();return true;")
                wait_until(lambda: "session resumed" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert live_state["opened"] == 2 and live_state["resumed"]
                assert api._chat._live._connection.logical_id == logical_id
                assert (home / "notes.json").read_bytes() == before_stop
                assert "NATIVE_SYNTHETIC_RESUME_HANDLE" not in window.evaluate_js("document.body.textContent")
                check_native_note_crud(home, window, js, wait_until, outcome, "live", "Live UI synthetic note")
                before_stop = (home / "notes.json").read_bytes()
                js("document.getElementById('inp').value='Native Stop';document.getElementById('send').click();return true;")
                assert live_state["waiting"].wait(5)
                assert not window.evaluate_js("document.getElementById('stopTask').disabled")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: "Stopped. Completed actions" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert live_state["closed"] and (home / "notes.json").read_bytes() == before_stop
                js("document.getElementById('inp').value='After stop';document.getElementById('send').click();return true;")
                wait_until(lambda: "new session" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert live_state["opened"] == 3 and not live_state["closed"]
                # Gerçek mute ve yalnız kuyrukta kalan sesi Stop: model tamamlanmış
                # olduğundan yeni bir native/model iptali başlatılmamalıdır.
                js("document.getElementById('mute').click();return true;")
                assert js("const a=await import('./js/live_audio.js');return a.liveAudio.muted;") is True
                js("document.getElementById('inp').value='Native audio muted';document.getElementById('send').click();return true;")
                wait_until(lambda: "playback muted" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                js("document.getElementById('mute').click();document.getElementById('inp').value='Native playback only';"
                   "document.getElementById('send').click();return true;")
                wait_until(lambda: "Native playback only reply" in window.evaluate_js("document.getElementById('msgs').textContent"))
                assert not api._chat.busy and window.evaluate_js("document.getElementById('send').disabled")
                last_audio_id = window.evaluate_js("window.nativeAudioPackets.at(-1).id")
                assert window.evaluate_js("window.nativeAudioPackets.length>0 && window.nativeAudioPackets.every(p=>p.accepted)")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: "playback stopped" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert js("return window.vex.audioChunk(" + json.dumps({"request_id": last_audio_id,
                    "mime_type": "audio/pcm;rate=24000", "data": "AAA="}) + ");") is False
                js("document.getElementById('inp').value='Native key switch';document.getElementById('send').click();return true;")
                wait_until(lambda: "Native key switch reply" in window.evaluate_js("document.getElementById('msgs').textContent"))
                assert window.evaluate_js("document.getElementById('send').disabled")
                js("const api=await import('./js/api.js');api.setConnectionStatus('offline','KEY CHANGED');"
                   "window.dispatchEvent(new Event('taskvex-key-saved'));return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert "KEY CHANGED" in window.evaluate_js("document.getElementById('netP').textContent")
                js("const c=await import('./js/connections.js');c.setCatalog({models:[{id:'gemini-3.8-live',name:'Synthetic Live'}],currentModel:'gemini-3.8-live'});return true;")
                # Fiziksel mikrofon açma: gerçek AudioWorklet/PCM yoluna
                # yalnız test oscillator stream'i ver; gerçek hesap kullanılmaz.
                js("window.testMicContext=new AudioContext();window.testMicOsc=testMicContext.createOscillator();window.testMicDestinations=[];"
                   "testMicOsc.start();await testMicContext.resume();"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=testMicContext.createMediaStreamDestination();testMicDestinations.push(d);"
                   "if(testMicDestinations.length===1)testMicOsc.connect(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Native microphone answer' in window.evaluate_js("document.getElementById('msgs').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Native microphone hello' in window.evaluate_js("document.getElementById('msgs').textContent")
                wait_until(lambda: window.evaluate_js("testMicDestinations.length>=2"))
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js("testMicDestinations[0].stream.getTracks().every(t=>t.readyState==='ended')")
                # İlk konuşma kaynağı ve yanıt dinleyicisi dışında üçüncü bir
                # mikrofon açılmamalı; yanıt sonunda aynı track canlı kalır.
                assert window.evaluate_js("testMicDestinations.length===2 && testMicDestinations[1].stream.getTracks().every(t=>t.readyState==='live')")
                outcome['reply_end_preserved_waiting_microphone_without_reopen'] = True
                js("testMicOsc.connect(testMicDestinations.at(-1));return true;")
                wait_until(lambda: window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length===3"))
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                js("testMicOff();testMicOsc.stop();await testMicContext.close();return true;")
                assert window.evaluate_js("testMicDestinations.every(d=>d.stream.getTracks().every(t=>t.readyState==='ended'))")
                outcome['two_voice_turns_automatic_rearm_without_second_click'] = True
                outcome['microphone_stream_worklet_pcm_transcript_and_cleanup'] = True
                # Kullanıcı On tercihi Stop/model reddinden bağımsızdır.
                # Sessizlikte yeniden API isteği olmadan yeni konuşma beklenir.
                js("window.persistentMicContext=new AudioContext();window.persistentMicOsc=persistentMicContext.createOscillator();"
                   "window.persistentMicDestinations=[];persistentMicOsc.start();await persistentMicContext.resume();"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=persistentMicContext.createMediaStreamDestination();persistentMicDestinations.push(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                unchanged_notes = (home / 'notes.json').read_bytes()
                js("document.getElementById('inp').value='Native microphone rejected note';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                assert window.evaluate_js("document.getElementById('micB').textContent.includes('Microphone On')")
                assert (home / 'notes.json').read_bytes() == unchanged_notes
                sent_after_error = len(live_state['sent'])
                time.sleep(.3)
                assert len(live_state['sent']) == sent_after_error  # Eski komut/retry yok.
                js("document.getElementById('inp').value='Native barge waiting';document.getElementById('send').click();return true;")
                wait_until(lambda: api._chat.busy and js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                js("window.stopMicStates=[];window.stopMicObserver=new MutationObserver(()=>stopMicStates.push(document.getElementById('micB').classList.contains('on')));"
                   "stopMicObserver.observe(document.getElementById('micB'),{attributes:true,attributeFilter:['class']});return true;")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: not api._chat.busy and not window.evaluate_js("document.getElementById('send').disabled"))
                wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                assert window.evaluate_js("document.getElementById('micB').getAttribute('aria-pressed')==='true' && window.vex.state==='idle'")
                assert js("stopMicObserver.disconnect();return !stopMicStates.includes(false);")
                assert window.evaluate_js("document.getElementById('netP').classList.contains('idle') && !document.getElementById('netP').classList.contains('off')")
                assert 'LIVE READY' in window.evaluate_js("document.getElementById('netP').textContent")
                assert js("document.getElementById('netP').click();return document.getElementById('netP').classList.contains('idle');")
                outcome['stop_microphone_light_stable_and_connection_neutral'] = True
                js("document.getElementById('inp').value='Native server interruption';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert window.evaluate_js("document.getElementById('netP').classList.contains('idle') && !document.getElementById('netP').classList.contains('off')")
                assert 'Native interrupted reply' in window.evaluate_js("document.getElementById('msgs').textContent")
                outcome['confirmed_server_interruption_neutral_not_transport_failure'] = True
                previous_voice_answers = window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length")
                js("persistentMicOsc.connect(persistentMicDestinations.at(-1));return true;")
                wait_until(lambda: window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length") > previous_voice_answers)
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                # Off kararı daha sonraki Stop veya model-ready olayıyla kaldırılmaz.
                wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                js("document.getElementById('inp').value='Native barge waiting';document.getElementById('send').click();return true;")
                wait_until(lambda: api._chat.busy and js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                js("testMicOff();return true;")
                time.sleep(.1)
                assert api._chat.busy and window.evaluate_js("document.getElementById('send').disabled")
                assert js("return document.querySelector('#msgs .m.j[data-request-id]:last-child').dataset.state;") == 'live'
                outcome['microphone_off_preserves_active_output_until_explicit_stop'] = True
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                js("window.dispatchEvent(new CustomEvent('taskvex-live-model-ready',{detail:{ready:true}}));return true;")
                assert js("const m=await import('./js/live_mic.js');return !m.liveMic.active && document.getElementById('micB').textContent.includes('Microphone Off');")
                js("persistentMicOsc.stop();await persistentMicContext.close();return true;")
                outcome['microphone_on_survives_rejected_note_and_stop_without_replay'] = True
                outcome['manual_microphone_off_survives_stop_and_model_ready'] = True
                # Gerçek AudioWorklet ile sessiz bekleme/konuşma/yanıt ayrımı.
                # Hybrid EOS artık erken yanıtlatabilir; sunucu cevabını açık
                # bariyerde tutarak Thinking ve kilitleri deterministik gözle.
                live_state['hold_microphone_reply'] = True
                live_state['hold_status_reply'] = True
                js("window.statusContext=new AudioContext();window.statusOsc=statusContext.createOscillator();window.statusDestinations=[];"
                   "statusOsc.start();await statusContext.resume();"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=statusContext.createMediaStreamDestination();statusDestinations.push(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js('window.vex.state') == 'idle'
                js("statusOsc.connect(statusDestinations.at(-1));return true;")
                wait_until(lambda: api._chat.busy and window.evaluate_js('window.vex.state') == 'listening')
                js("statusOsc.disconnect();return true;")
                wait_until(lambda: window.evaluate_js('window.vex.state') == 'thinking')
                assert api._chat.busy and window.evaluate_js("document.getElementById('send').disabled")
                live_state['hold_status_reply'] = False
                wait_until(lambda: window.evaluate_js('window.vex.state') == 'speaking')
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js('window.vex.state') == 'idle'
                js("testMicOff();statusOsc.stop();await statusContext.close();return true;")
                live_state['hold_microphone_reply'] = False
                outcome['idle_waiting_listening_speech_thinking_and_speaking'] = True
                # Mic Off yalnız EOS yollar; aktif model turu Stop sayılmaz.
                live_state['hold_microphone_reply'] = True
                ended_before = live_state.get('input_ended', 0)
                live_state['voice_seen'] = False
                js("window.offContext=new AudioContext();window.offOsc=offContext.createOscillator();offOsc.start();"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=offContext.createMediaStreamDestination();offOsc.connect(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: api._chat.busy and live_state.get('voice_seen'))
                js("testMicOff();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert live_state.get('input_ended', 0) == ended_before + 1
                assert 'Native microphone Off answer' in window.evaluate_js("document.getElementById('msgs').textContent")
                assert 'Stopped' not in window.evaluate_js("document.getElementById('textStatus').textContent")
                assert window.evaluate_js("document.getElementById('micB').getAttribute('aria-pressed')==='false'")
                js("offOsc.stop();await offContext.close();return true;")
                live_state['hold_microphone_reply'] = False
                outcome['microphone_off_ends_input_without_stopping_answer'] = True
                # Setup bitmeden Off da aynı giriş sonu yolunu kullanır.
                assert api._chat.reset_live()
                live_state.update(hold_setup=True, setup_waiting=False, hold_microphone_reply=True)
                ended_before = live_state.get('input_ended', 0)
                js("window.earlyContext=new AudioContext();window.earlyOsc=earlyContext.createOscillator();earlyOsc.start();"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=earlyContext.createMediaStreamDestination();earlyOsc.connect(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: live_state.get('setup_waiting'))
                js("testMicOff();return true;")
                live_state['hold_setup'] = False
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert live_state.get('input_ended', 0) == ended_before + 1
                assert 'Stopped' not in window.evaluate_js("document.getElementById('textStatus').textContent")
                js("earlyOsc.stop();await earlyContext.close();return true;")
                live_state['hold_microphone_reply'] = False
                outcome['microphone_off_before_setup_ends_input_without_stop'] = True
                # Aynı gerçek WebView mikrofonu eski yanıtı keser; yeni tur
                # yalnız host'un eski araç sonucunu kesinleştirmesinden sonra açılır.
                for prompt in ['Native barge active', 'Native barge playback']:
                    previous_answers = window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length")
                    js("window.bargeContext=new AudioContext();window.bargeOsc=bargeContext.createOscillator();window.bargeDestinations=[];"
                       "bargeOsc.start();await bargeContext.resume();"
                       "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                       "const d=bargeContext.createMediaStreamDestination();bargeDestinations.push(d);return d.stream;}});"
                       "testMicOn();return true;")
                    wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                    js("document.getElementById('inp').value=" + json.dumps(prompt) + ";document.getElementById('send').click();return true;")
                    wait_until(lambda: window.evaluate_js("document.getElementById('send').disabled && document.getElementById('micB').classList.contains('on')"))
                    wait_until(lambda: js("const m=await import('./js/live_mic.js');return m.liveMic.waitingForSpeech;"))
                    old_reply_id = window.evaluate_js("document.querySelector('#msgs .m.j[data-request-id]:last-child')?.dataset.requestId")
                    assert old_reply_id
                    if prompt.endswith('active'):
                        assert api._chat.busy
                        assert 'Native barge active reply' in window.evaluate_js("document.getElementById('msgs').textContent")
                        assert js("return document.querySelector('[data-request-id=' + JSON.stringify(" + json.dumps(old_reply_id) + ") + '].j').dataset.state;") == 'live'
                        outcome['live_transcript_visible_before_turn_completion'] = True
                    # Kısa bir 100 ms darbe eski yanıtı kesmemeli veya yeni bir
                    # konuşma başlatmamalı; ardından gerçek süreli aday denenir.
                    js("bargeOsc.connect(bargeDestinations.at(-1));await new Promise(r=>setTimeout(r,100));"
                       "bargeOsc.disconnect();await new Promise(r=>setTimeout(r,200));return true;")
                    assert window.evaluate_js("document.getElementById('send').disabled")
                    assert window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length") == previous_answers
                    assert js("return document.querySelector('[data-request-id=' + JSON.stringify(" + json.dumps(old_reply_id) + ") + '].j').dataset.state;") != 'interrupted'
                    js("bargeOsc.connect(bargeDestinations.at(-1));return true;")
                    wait_until(lambda: window.evaluate_js("document.getElementById('msgs').textContent.split('Native microphone answer').length") > previous_answers)
                    wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                    assert not api._chat.busy
                    assert js("const nodes=Array.from(document.querySelectorAll('#msgs .m.j')).filter(n=>n.dataset.requestId===" + json.dumps(old_reply_id) + ");return nodes.length===1 && nodes[0].dataset.state==='interrupted' && nodes[0].textContent.includes('reply');")
                    if prompt.endswith('active'):
                        from app.storage.json_store import JsonStore
                        assert sum(n['text']=='Committed before barge-in' for n in (JsonStore(home/'notes.json').read() or {})['notes']) == 1
                    js("testMicOff();bargeOsc.stop();await bargeContext.close();return true;")
                    assert window.evaluate_js("bargeDestinations.every(d=>d.stream.getTracks().every(t=>t.readyState==='ended'))")
                outcome['barge_in_active_preserved_commit_and_playback_handoff'] = True
                outcome['short_noise_did_not_interrupt_active_or_playback_reply'] = True
                outcome['live_transcript_interrupted_text_preserved_without_duplicate'] = True
                assert 'Failed to send live_audio_start: Live response stopped' not in window.evaluate_js("document.getElementById('log').textContent")
                outcome['normal_stop_not_logged_as_transport_failure'] = True
                js("window.bargeContext=new AudioContext();window.bargeOsc=bargeContext.createOscillator();window.bargeDestinations=[];"
                   "bargeOsc.start();await bargeContext.resume();window.newBargeTurns=0;window.bargeOriginalEvent=window.pywebview.api.event;"
                   "window.pywebview.api.event=(name,data)=>{if(name==='live_audio_start')window.newBargeTurns++;"
                   "if(name==='stop_task')return new Promise(resolve=>{window.releaseBargeStop=()=>bargeOriginalEvent(name,data).then(resolve);});"
                   "return bargeOriginalEvent(name,data);};"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=bargeContext.createMediaStreamDestination();bargeDestinations.push(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                js("document.getElementById('inp').value='Native barge waiting';document.getElementById('send').click();return true;")
                wait_until(lambda: js("const m=await import('./js/live_mic.js');return document.getElementById('send').disabled && m.liveMic.waitingForSpeech;"))
                js("bargeOsc.connect(bargeDestinations.at(-1));return true;")
                wait_until(lambda: window.evaluate_js("typeof window.releaseBargeStop==='function'"))
                assert api._chat.busy and window.evaluate_js('window.newBargeTurns') == 0
                js("document.getElementById('disc').click();releaseBargeStop();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert window.evaluate_js('window.newBargeTurns') == 0
                assert window.evaluate_js("bargeDestinations.every(d=>d.stream.getTracks().every(t=>t.readyState==='ended'))")
                js("window.pywebview.api.event=bargeOriginalEvent;bargeOsc.stop();await bargeContext.close();return true;")
                outcome['barge_in_waited_for_real_completion_disconnect_dropped_buffer'] = True
                mic_packets = len(live_state['sent'])
                js("Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{throw new Error('Synthetic denied');}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'permission denied' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert not window.evaluate_js("document.getElementById('send').disabled")
                assert window.evaluate_js("document.getElementById('micB').classList.contains('on')")
                js("window.cancelMicContext=new AudioContext();window.cancelMicDestinations=[];"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=cancelMicContext.createMediaStreamDestination();cancelMicDestinations.push(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js("cancelMicDestinations[0].stream.getTracks().every(t=>t.readyState==='ended')")
                assert window.evaluate_js("cancelMicDestinations.at(-1).stream.getTracks().every(t=>t.readyState==='live')")
                assert not any('tool_response' in p for p in live_state['sent'][mic_packets:])
                js("testMicOff();await cancelMicContext.close();return true;")
                outcome['microphone_permission_denied_and_stop_discard'] = True
                # Otomatik listeleme getUserMedia çağırmamalı; izin Mic'e aittir.
                js("window.deviceContext=new AudioContext();window.deviceStream=deviceContext.createMediaStreamDestination().stream;"
                   "window.deviceList=[{kind:'audioinput',deviceId:'12345',label:'Synthetic microphone'},"
                   "{kind:'audiooutput',deviceId:'missing-test-output',label:'Synthetic speaker'}];"
                   "Object.defineProperty(navigator.mediaDevices,'enumerateDevices',{configurable:true,value:async()=>deviceList});"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async(options)=>{window.lastMicOptions=options;return deviceStream;}});"
                   "const p=await import('./js/panels.js');p.openM('mSet');return true;")
                wait_until(lambda: 'Audio devices listed' in window.evaluate_js("document.getElementById('devMsg').textContent"))
                wait_until(lambda: window.evaluate_js("Array.from(document.getElementById('dIn').options).some(o=>o.value==='12345')"))
                assert window.evaluate_js("window.lastMicOptions===undefined && deviceStream.getTracks().every(t=>t.readyState==='live')")
                js("document.getElementById('dIn').value='12345';document.getElementById('dIn').onchange();"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js("lastMicOptions.audio.deviceId.exact==='12345'")
                js("window.deviceList=deviceList.filter(d=>d.kind!=='audioinput');navigator.mediaDevices.dispatchEvent(new Event('devicechange'));return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Selected microphone was removed' in window.evaluate_js("document.getElementById('textStatus').textContent")
                assert window.evaluate_js("document.getElementById('micB').textContent").strip() == 'Microphone On'
                assert window.evaluate_js("deviceStream.getTracks().every(t=>t.readyState==='ended')")
                assert not window.evaluate_js("document.getElementById('send').disabled")
                wait_until(lambda: 'Saved device unavailable' in window.evaluate_js("document.getElementById('dIn').selectedOptions[0].textContent"))
                js("document.getElementById('dIn').value='default';document.getElementById('dIn').onchange();"
                   "document.getElementById('dOut').value='missing-test-output';document.getElementById('dOut').onchange();"
                   "const s=await import('./js/settings.js');return await s.saveSettingsConfirmed();")
                assert api._store.read()['devs']['dIn'] == 'default'
                assert api._store.read()['devs']['dOut'] == 'missing-test-output'
                # Var olmayan sink gerçek Web Audio'da reddedilmeli; metin
                # sonucu korunurken başka çıkışta sessizce çalınmamalıdır.
                js("document.getElementById('inp').value='Native audio muted';document.getElementById('send').click();return true;")
                wait_until(lambda: 'Selected speaker unavailable' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Native audio muted reply' in window.evaluate_js("document.getElementById('msgs').textContent")
                before_route_stop = len(live_state['sent'])
                js("window.originalSink=AudioContext.prototype.setSinkId;"
                   "AudioContext.prototype.setSinkId=function(){window.routeWaiting=true;return new Promise(()=>{});};"
                   "document.getElementById('dOut').append(new Option('Pending synthetic sink','pending-test-output'));"
                   "document.getElementById('dOut').value='pending-test-output';document.getElementById('dOut').onchange();"
                   "document.getElementById('inp').value='Do not send during sink setup';document.getElementById('send').click();return true;")
                wait_until(lambda: window.evaluate_js("window.routeWaiting===true"))
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Stopped' in window.evaluate_js("document.getElementById('textStatus').textContent")
                assert len(live_state['sent']) == before_route_stop
                js("if(originalSink)AudioContext.prototype.setSinkId=originalSink;else delete AudioContext.prototype.setSinkId;return true;")
                outcome['stop_during_output_setup_did_not_send_model_request'] = True
                js("document.getElementById('dOut').value='default';document.getElementById('dOut').onchange();return true;")
                # Varsayılan sink'e gerçek API çağrısı; fiziksel cihaz değişmez.
                outcome['web_audio_custom_output_supported'] = js("const c=new AudioContext();let supported=typeof c.setSinkId==='function';"
                          "if(supported)await c.setSinkId('');await c.close();return supported;")
                js("await deviceContext.close();return true;")
                outcome['audio_device_scan_exact_input_missing_sink_and_persistence'] = True
                # Gerçek profil formu -> doğrulanmış disk -> REST/Live SDK setup.
                # Yanıtlar sentetiktir; doğru dili konuştuğu iddia edilmez.
                js("const p=await import('./js/panels.js');p.openM('mProf');"
                   "document.getElementById('pLang').value='en';document.getElementById('pIns').value='Native preference probe';"
                   "document.getElementById('pMem').value='Native unused memory';document.getElementById('btnSaveProf').click();return true;")
                wait_until(lambda: api._store.read().get('prof', {}).get('pIns') == 'Native preference probe')
                wait_until(lambda: not window.evaluate_js("document.getElementById('mProf').classList.contains('o')"))
                js("document.getElementById('liveLatencyTest').checked=false;document.getElementById('inp').value='Native profile probe';"
                   "document.getElementById('send').click();return true;")
                wait_until(lambda: 'Native profile probe REST' in window.evaluate_js("document.getElementById('msgs').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                rest_instruction = ''.join(p['text'] for p in text_payloads[-1]['systemInstruction']['parts'])
                assert 'English (en)' in rest_instruction and 'Native preference probe' in rest_instruction
                assert 'Native unused memory' not in rest_instruction
                js("document.getElementById('liveLatencyTest').checked=true;document.getElementById('inp').value='Native profile probe';"
                   "document.getElementById('send').click();return true;")
                wait_until(lambda: 'Native profile probe Live' in window.evaluate_js("document.getElementById('msgs').textContent"))
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                live_instruction = ''.join(p['text'] for p in [m['setup'] for m in live_state['sent'] if 'setup' in m][-1]['systemInstruction']['parts'])
                assert rest_instruction == live_instruction
                old_profile_session = api._chat._live._connection.logical_id
                old_opened = live_state['opened']
                js("const p=await import('./js/panels.js');p.openM('mProf');"
                   "document.getElementById('pLang').value='tr';document.getElementById('pIns').value='Native new preference';"
                   "document.getElementById('btnSaveProf').click();return true;")
                wait_until(lambda: api._store.read().get('prof', {}).get('pLang') == 'tr')
                wait_until(lambda: not window.evaluate_js("document.getElementById('mProf').classList.contains('o')"))
                js("document.getElementById('inp').value='Native profile probe';document.getElementById('send').click();return true;")
                wait_until(lambda: live_state['opened'] == old_opened + 1)
                wait_until(lambda: not api._chat.busy and not window.evaluate_js("document.getElementById('send').disabled"))
                profile_setup = [m['setup'] for m in live_state['sent'] if 'setup' in m][-1]
                instruction = ''.join(p['text'] for p in profile_setup['systemInstruction']['parts'])
                assert 'Turkish (tr)' in instruction and 'Native new preference' in instruction
                assert 'handle' not in profile_setup['sessionResumption']
                assert api._chat._live._connection.logical_id != old_profile_session
                assert 'scope_changed' in window.evaluate_js("document.getElementById('textStatus').textContent")
                outcome['saved_profile_form_shared_rest_live_instruction_and_scope_reset'] = True
                # Gerçek New Chat düğmesi/bridge; hatırlama yalnız sentetik
                # sunucunun gerçekten aldığı history verisinden üretilir.
                js("testMicOff();document.getElementById('inp').value='Native temporary name is Ada';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                preserved_notes = (home / 'notes.json').read_bytes()
                js("document.getElementById('inp').value='Native Stop';document.getElementById('send').click();return true;")
                wait_until(lambda: api._chat.busy)
                assert window.evaluate_js("document.getElementById('newChat').disabled")
                js("document.getElementById('stopTask').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                js("document.getElementById('inp').value='Native memory ask';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Native remembered name: Ada' in window.evaluate_js("document.getElementById('msgs').textContent")
                assert 'recent conversation restored' in window.evaluate_js("document.getElementById('textStatus').textContent")
                memory_before = api._chat._memory.snapshot()
                js("window.confirm=()=>false;document.getElementById('newChat').click();return true;")
                assert api._chat._memory.snapshot() == memory_before
                js("window.confirm=()=>true;document.getElementById('newChat').click();return true;")
                wait_until(lambda: 'New chat. Temporary' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert not api._chat._memory.snapshot()
                assert window.evaluate_js("document.getElementById('msgs').childElementCount") == 0
                assert (home / 'notes.json').read_bytes() == preserved_notes
                js("document.getElementById('inp').value='Native memory ask';document.getElementById('send').click();return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('send').disabled"))
                assert 'Native remembered name: unknown' in window.evaluate_js("document.getElementById('msgs').textContent")
                outcome['temporary_memory_after_stop_new_chat_confirmation_and_notes_preserved'] = True
                check_local_sleep(window, api, js, wait_until, live_state, wake_state, outcome)
                check_native_note_batches(api, home, window, js, wait_until, outcome)
                check_native_shutdown_request(window, api, js, wait_until, outcome)
                check_native_clocks(window, api, js, wait_until, outcome)
                js("const a=await import('./js/api.js');for(let i=0;i<250;i++)a.addLog('Native bounded entry '+i);return true;")
                assert window.evaluate_js("document.getElementById('log').childElementCount") == 200
                outcome['engine_log_bounded_to_200_entries'] = True
                js("document.getElementById('disc').click();return true;")
                # Socket, loop/thread temizliğinden önce kapanır. Ara durumu
                # bitiş sanma; host tüm kaynakları bırakana kadar bekle.
                wait_until(lambda: live_state["closed"] and api._chat._live._thread is None)
                assert api._chat._live._thread is None
                original_run_live = api._chat.run_live
                api._chat.run_live = lambda text, model, **kwargs: {
                    **original_run_live(text, model, **kwargs), 'ok':False, 'unknown':True}
                js("window.unknownContext=new AudioContext();window.unknownOsc=unknownContext.createOscillator();window.unknownDestinations=[];"
                   "unknownOsc.start();await unknownContext.resume();window.unknownNewTurns=0;window.unknownOriginalEvent=window.pywebview.api.event;"
                   "window.pywebview.api.event=(name,data)=>{if(name==='live_audio_start')window.unknownNewTurns++;return unknownOriginalEvent(name,data);};"
                   "Object.defineProperty(navigator.mediaDevices,'getUserMedia',{configurable:true,value:async()=>{"
                   "const d=unknownContext.createMediaStreamDestination();unknownDestinations.push(d);return d.stream;}});"
                   "testMicOn();return true;")
                wait_until(lambda: 'Listening for speech' in window.evaluate_js("document.getElementById('textStatus').textContent"))
                js("document.getElementById('inp').value='Native barge waiting';document.getElementById('send').click();return true;")
                wait_until(lambda: js("const m=await import('./js/live_mic.js');return document.getElementById('send').disabled && m.liveMic.waitingForSpeech;"))
                js("unknownOsc.connect(unknownDestinations.at(-1));return true;")
                wait_until(lambda: "Result unknown" in window.evaluate_js("document.getElementById('textStatus').textContent"))
                assert window.evaluate_js("document.getElementById('send').disabled && document.getElementById('noteAdd').disabled")
                assert window.evaluate_js('window.unknownNewTurns') == 0
                assert window.evaluate_js("unknownDestinations.every(d=>d.stream.getTracks().every(t=>t.readyState==='ended'))")
                assert window.evaluate_js("document.getElementById('micB').getAttribute('aria-pressed')==='true'")
                js("testMicOff();document.getElementById('micB').click();return true;")
                assert js("const m=await import('./js/live_mic.js');return !m.liveMic.active && document.getElementById('send').disabled;")
                assert window.evaluate_js('window.unknownNewTurns') == 0
                js("window.pywebview.api.event=unknownOriginalEvent;unknownOsc.stop();await unknownContext.close();return true;")
                api._chat.run_live = original_run_live
                outcome['barge_in_unknown_result_dropped_buffer_and_locked_controls'] = True
                outcome.update(ok=True, phase=phase, native=initial, native_chat=True, fallback=True,
                               single_note=True, safe_dom=True, concurrent_rejected=True,
                               bridge_responsive=True, failure_preserved_input=True,
                               model_change_not_online=True, unknown_locked=True, chat_before_notes_confirmation=True,
                               dynamic_live_catalog=True, text_model_separate=True, safe_http_diagnostics=True,
                               live_latency_probe=True, live_no_rest_fallback=True, live_plain_chat_notes_unchanged=True,
                               live_tool_saved=True, live_tool_panel_refreshed=True, live_tool_replay_single_write=True,
                               live_stop_button=True, live_stop_preserved_notes=True, live_stop_next_session_fresh=True,
                               rest_stop_button=True, rest_stop_waited_for_http=True, rest_stop_blocked_late_tool=True,
                               live_goaway_resumed=True, live_resume_scope_preserved=True, live_resume_token_hidden=True,
                               live_session_reused=True, disconnect_closed_live_io=True)
                outcome.update(live_pcm_forwarded=True, live_mute=True, playback_stop_after_model_done=True,
                               audio_drain_before_unlock=True, stale_audio_ignored=True, audio_stale_online_ignored=True)
                return
            if phase == "credentials":
                from app.storage import credentials
                import ctypes as c
                from ctypes import wintypes as w

                store = api._credentials
                assert store.read() is None, "Synthetic profile must not contain an existing credential"
                try:
                    assert key_query_started.wait(5)
                    js("window.keyEvents=[];"
                       "window.vex.onEvent=(name,data)=>{if(name==='apikey')window.keyEvents.push(data);};"
                       "document.getElementById('apiKeyIn').value='TASKVEX_SYNTHETIC_KEY';"
                       "document.getElementById('saveApiKey').click();return true;")
                    wait_until(lambda: store.read() == "TASKVEX_SYNTHETIC_KEY")
                    wait_until(lambda: "Key stored locally" in window.evaluate_js("document.getElementById('apiKeyStatus').textContent"))
                    state = js("const settings=await import('./js/settings.js');return {"
                               "empty:document.getElementById('apiKeyIn').value==='',"
                               "secretAbsent:!JSON.stringify([localStorage,settings.store]).includes('TASKVEX_SYNTHETIC_KEY'),"
                               "observer:window.keyEvents,online:document.getElementById('netP').textContent,"
                               "pending:Object.keys(window.pywebview._returnValuesCallbacks.event)};")
                    assert state["empty"] and state["secretAbsent"] and state["observer"] == ["[REDACTED]"]
                    assert "OFFLINE" in state["online"]
                    assert state["pending"]
                    release_key_query.set()
                    # PyWebView 6.2.1 callback kaydının silinmesi yanıtın JS'ye
                    # ulaştığını kanıtlar; başta gözlemci bulunması gerekmez.
                    wait_until(lambda: window.evaluate_js(json.dumps(state["pending"]) +
                               ".every(id=>!(id in window.pywebview._returnValuesCallbacks.event))"))
                    assert "Key stored locally" in window.evaluate_js("document.getElementById('apiKeyStatus').textContent")
                    assert api.event("query_apikey") == {"ok": True, "completed": True, "configured": True}
                    environment = dict(os.environ)
                    environment.pop("GEMINI_API_KEY", None)
                    checked = subprocess.run([sys.executable, "-c",
                        "from app.storage.credentials import load_gemini_key; "
                        "print(load_gemini_key() == 'TASKVEX_SYNTHETIC_KEY')"],
                        env=environment, capture_output=True, text=True, timeout=15)
                    assert checked.returncode == 0 and checked.stdout.strip() == "True"

                    original_write = store.write
                    def fail_key(value):
                        raise credentials.CredentialError("TASKVEX_SYNTHETIC_FAILURE_SECRET")
                    store.write = fail_key
                    js("document.getElementById('apiKeyIn').value='TASKVEX_SYNTHETIC_FAILURE_SECRET';"
                       "document.getElementById('saveApiKey').click();return true;")
                    wait_until(lambda: "Key save was not confirmed" in window.evaluate_js("document.getElementById('apiKeyStatus').textContent"))
                    assert store.read() == "TASKVEX_SYNTHETIC_KEY"
                    store.write = original_write
                    safe = js("const api=await import('./js/api.js');"
                              "const original=window.pywebview.api.event;let result;"
                              "try{window.pywebview.api.event=async()=>{throw new Error('TASKVEX_SYNTHETIC_FAILURE_SECRET');};"
                              "result=await api.emit('apikey','TASKVEX_SYNTHETIC_FAILURE_SECRET');}"
                              "finally{window.pywebview.api.event=original;}"
                              "return {ok:result.ok,response:result.response,log:document.getElementById('log').textContent};")
                    assert safe["ok"] is False and safe["response"] is None
                    assert "TASKVEX_SYNTHETIC_FAILURE_SECRET" not in safe["log"]
                    fallback = js("const api=await import('./js/api.js');const original=window.pywebview;"
                                  "let result;window.keyEvents=[];try{window.pywebview=null;"
                                  "result=await api.emit('apikey','TASKVEX_SYNTHETIC_FAILURE_SECRET');}"
                                  "finally{window.pywebview=original;}return {ok:result.ok,events:window.keyEvents};")
                    assert fallback == {"ok": False, "events": []}
                    outcome.update(ok=True, phase=phase, credential_write_read=True,
                                   cross_process_load=True, input_cleared=True, no_key_in_local_storage=True,
                                   observer_redacted=True, native_error_redacted=True,
                                   browser_fallback_blocked=True, failure_preserved_old_key=True,
                                   save_did_not_mark_online=True, stale_status_ignored=True)
                finally:
                    release_key_query.set()
                    # Yalnız bu geçici profilin sentetik kaydını temizle.
                    library = credentials._library()
                    library.CredDeleteW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD]
                    library.CredDeleteW.restype = w.BOOL
                    deleted = library.CredDeleteW(store._target, 1, 0)
                    assert deleted or c.get_last_error() == 1168
                return
            if phase == "save":
                wait_until(lambda: window.evaluate_js("document.getElementById('notesConnect').textContent==='Use backend notes'"))
                assert not (home / "notes.json").exists()
                js("window.confirm=()=>false;document.getElementById('notesConnect').click();return true;")
                assert not (home / "notes.json").exists()
                js("window.confirm=()=>true;document.getElementById('notesConnect').click();return true;")
            wait_until(lambda: api._notes_ready)
            wait_until(lambda: not window.evaluate_js("document.getElementById('noteAdd').disabled"))
            if phase == "notes":
                check_native_note_ui(home, window, js, wait_until, outcome)
                return
            if phase == "export_cancel":
                original_export = (home / "exported-backup.json").read_bytes()
                assert export_backup(False) is None
                assert (home / "exported-backup.json").read_bytes() == original_export
                assert "download requested" in window.evaluate_js("document.getElementById('saveStatus').textContent").lower()
                outcome.update(ok=True, phase=phase, export_cancel_preserved_file=True)
                return
            if phase == "persistence":
                queue = js("const s=await import('./js/settings.js'); const original=window.pywebview.api.event;"
                           "window.vex.onSave=snapshot=>{snapshot.theme='#000000';};"
                           "let active=0,maxActive=0;const themes=[];"
                           "window.pywebview.api.event=async(name,data)=>{if(name!=='save')return original(name,data);"
                           "active++;maxActive=Math.max(active,maxActive);themes.push(data.theme);"
                           "try{await new Promise(r=>setTimeout(r,30));return await original(name,data);}finally{active--;}};"
                           "try{s.store.theme='#4fd8ff';s.saveAll();s.store.theme='#5dffb0';s.saveAll();"
                           "return {ok:await s.saveSettingsConfirmed(),maxActive,themes};}finally{window.pywebview.api.event=original;window.vex.onSave=null;}")
                assert queue == {"ok": True, "maxActive": 1, "themes": ["#4fd8ff", "#5dffb0", "#5dffb0"]}, queue
                assert api._store.read()["theme"] == "#5dffb0"
                backup = {"theme": "#5dffb0", "notes": ["Native local note", "Imported note"],
                          "skills": [{"id": "import-skill", "name": "Imported skill", "steps": []}],
                          "routines": [{"id": "import-routine", "name": "Imported routine", "type": "manual", "steps": "Keep step", "on": 0}]}
                ui_import = js("const input=document.getElementById('impF');const transfer=new DataTransfer();"
                               "window.alert=message=>{window._importAlert=message;};"
                               "transfer.items.add(new File([JSON.stringify(" + json.dumps(backup) + ")],'backup.json',{type:'application/json'}));"
                               "input.files=transfer.files;input.dispatchEvent(new Event('change'));"
                               "for(let n=0;n<100&&input.value;n++)await new Promise(r=>setTimeout(r,30));"
                               "const s=await import('./js/settings.js');return {alert:window._importAlert||null,notes:s.store.notes,skills:s.store.skills.length};")
                assert ui_import["alert"] is None and ui_import["skills"] == 1, ui_import
                assert [note["t"] for note in ui_import["notes"]] == ["Native local note", "Imported note"]
                before = js("const s=await import('./js/settings.js');return JSON.stringify(s.store);")
                raw = api._store.path.read_bytes()
                original_write = api._store.write

                def fail(data):
                    raise StoreError("write_failed", "Simulated native save failure")

                api._store.write = fail
                assert js("const s=await import('./js/settings.js');return await s.importBackup({theme:'#ff5d5d',notes:['Must not apply']});") is False
                assert js("const s=await import('./js/settings.js');return JSON.stringify(s.store);") == before
                assert api._store.path.read_bytes() == raw
                api._store.write = original_write
                assert js("const s=await import('./js/settings.js');return await s.importBackup({notes:[null]});") is False
                partial = js("const s=await import('./js/settings.js');const raw=localStorage.getItem('taskvex_ui');"
                             "const original=Storage.prototype.setItem;let writes=0;"
                             "Storage.prototype.setItem=function(key,value){if(key==='taskvex_ui'&&++writes>=2)throw new DOMException('Full','QuotaExceededError');return original.call(this,key,value);};"
                             "try{return {ok:await s.importBackup({theme:'#4fd8ff',notes:['Must not replace local notes']}),"
                             "sameLocal:localStorage.getItem('taskvex_ui')===raw,notes:s.store.notes,theme:s.store.theme};}"
                             "finally{Storage.prototype.setItem=original;}")
                assert partial["ok"] is False and partial["sameLocal"] is True, partial
                assert partial["theme"] == "#5dffb0" and [n['t'] for n in partial['notes']] == ['Must not replace local notes']
                assert api._store.read()["theme"] == "#4fd8ff"
                # Ayrı depoların kısmi başarısını gizleme; sonraki açık Save ile
                # testin yerel mevcut ayarlarını tekrar native'e eşitliyoruz.
                assert js("const s=await import('./js/settings.js');return await s.saveSettingsConfirmed();") is True

                # Gerçek export -> import yolu metadata'yı hiçbir ara dönüşümde düşürmemeli.
                dated = {"t": "Timestamp backup", "d": 0, "id": "dated-backup",
                         "created_at": "2024-02-29T12:34:56.789Z"}
                assert js("const s=await import('./js/settings.js');return await s.importBackup(" +
                          json.dumps({"notes": [dated]}) + ");") is True
                dated_export = export_backup(True)
                assert dated_export is not None
                assert dated_export["notes"] == [dated] and dated_export["theme"] == "#5dffb0"
                assert json.loads((home / "notes.json").read_text("utf-8"))["data"]["notes"][0]["created_at"] == dated["created_at"]
                original_notes = (home / "notes.json").read_bytes()
                assert js("const s=await import('./js/settings.js');return await s.importBackup({theme:'#000000',"
                          "notes:[{t:'Invalid timestamp',d:0,created_at:'yesterday'}]});") is False
                assert (home / "notes.json").read_bytes() == original_notes
                # Sonraki açılış/kurtarma fazları için gerçek core restore ile
                # başlangıç notunu geri getir; eski setter yazma sahibi değildir.
                assert js("const n=await import('./js/notes.js');return await n.restoreNativeNotes([{t:'Native local note',d:0}]);") is True
                timeout = js("const s=await import('./js/settings.js');const original=window.pywebview.api.event;"
                             "let sent=0,resolveSave;window.pywebview.api.event=(name,data)=>name==='save'?(sent++,new Promise(r=>resolveSave=r)):original(name,data);"
                             "try{const ok=await s.saveSettingsConfirmed();resolveSave({ok:true,completed:true,saved:true});"
                             "await new Promise(r=>setTimeout(r,10));return {ok,sent,status:document.getElementById('saveStatus').textContent};}"
                             "finally{window.pywebview.api.event=original;}")
                assert timeout == {"ok": False, "sent": 1, "status": "Settings save not confirmed"}, timeout
                outcome.update(ok=True, phase=phase, ordered_save_queue=True, file_input_import=True,
                               native_rejection_preserved_ui=True, local_quota_rollback=True,
                               partial_commit_reported=True, actual_export_file=True, note_time_backup_roundtrip=True,
                               observer_cannot_mutate_save=True, timeout_no_repeat=True)
                return
            if phase == "save":
                controls = js("const settings=await import('./js/settings.js');"
                              "const context=new AudioContext(); await context.resume();"
                              "const audio=context.state; await context.close();"
                              "document.getElementById('inp').dispatchEvent(new KeyboardEvent('keydown',"
                              "{key:'F11',bubbles:true,cancelable:true}));"
                              "return {theme:settings.store.theme,audio};")
                assert controls == {"theme": "#a78bfa", "audio": "running"}, controls
                wait_until(lambda: captured["window"].native.is_fullscreen)
                js("document.getElementById('inp').dispatchEvent(new KeyboardEvent('keydown',"
                   "{key:'F11',repeat:true,bubbles:true,cancelable:true})); return true;")
                assert window.native.is_fullscreen
                js("document.getElementById('inp').dispatchEvent(new KeyboardEvent('keydown',"
                   "{key:'F11',bubbles:true,cancelable:true})); return true;")
                wait_until(lambda: not window.native.is_fullscreen)
                outcome.update(default_purple=True, audio_without_gesture=True, f11_toggle=True)
                assert js("const n=await import('./js/notes.js');if(!(await n.addNote('Native local note')))throw new Error('Note add failed');"
                          "window._events=[]; window.vex.onEvent=(name)=>window._events.push(name);"
                          "window.vex.setSkills([{id:'keep-skill',name:'Keep skill',steps:[]}]);"
                          "window.vex.setRoutines([{id:'keep-routine',name:'Keep routine',type:'manual',steps:'Keep step',on:0}]);"
                          "return window.vex.loadStore({theme:'#4fd8ff',prof:{pIns:'Native profile 📝'},"
                          "devs:{dIn:'7'},conn:{model:'gemini-3.8-flash'}});") is True
                assert js("return window._events.includes('save');") is False
                js("const checkbox=document.getElementById('onTop'); checkbox.checked=true;"
                   "checkbox.dispatchEvent(new Event('change')); return true;")
                wait_until(lambda: window.native.TopMost)
                js("const panels=await import('./js/panels.js'); panels.openM('mSet');"
                   "document.getElementById('btnSaveSet').click(); return true;")
                wait_until(lambda: (api._store.read() or {}).get("theme") == "#4fd8ff")
                wait_until(lambda: not window.evaluate_js("document.getElementById('mSet').classList.contains('o')"))
                saved = api._store.read()
                assert saved["prof"]["pIns"] == "Native profile 📝"
                assert "notes" not in saved
                assert saved["onTop"] is True
                previous = api._store.path.read_bytes()
                invalid = js("return await window.pywebview.api.event('save',{vol:9});")
                assert invalid["ok"] is False and api._store.path.read_bytes() == previous
                unsupported = js("return await window.pywebview.api.event('text','hello');")
                assert unsupported["ok"] is False
                outcome.update(settings_saved=True, invalid_save_preserved=True,
                               unsupported_rejected=True, snapshot_no_echo=True, native_on_top=True)
            else:
                restored = js("const settings=await import('./js/settings.js');"
                              "return {theme:settings.store.theme,profile:settings.store.prof.pIns,"
                              "notes:window.document.getElementById('notesL')?.textContent||"
                              "JSON.stringify(settings.store.notes)};")
                assert restored["theme"] == "#4fd8ff", restored
                assert restored["profile"] == "Native profile 📝", restored
                assert "Native local note" in restored["notes"], restored
                assert window.native.TopMost
                outcome["on_top_restored"] = True

                original_write = api._store.write
                def fail(data):
                    raise StoreError("write_failed", "Simulated test failure")

                api._store.write = fail
                js("const panels=await import('./js/panels.js'); panels.openM('mSet');"
                   "document.getElementById('btnSaveSet').click(); return true;")
                wait_until(lambda: "Failed to send save" in window.evaluate_js("document.getElementById('log').textContent"))
                assert window.evaluate_js("document.getElementById('mSet').classList.contains('o')")
                outcome.update(reopened_settings=True, local_note_preserved=True, failed_save_modal_open=True)
                before_reset = js("const settings=await import('./js/settings.js');"
                                  "return JSON.stringify([settings.store.notes,settings.store.skills,settings.store.routines,"
                                  "settings.store.prof,settings.store.devs,settings.store.conn]);")
                js("window.confirm=()=>true; document.getElementById('resetAll').click(); return true;")
                wait_until(lambda: not window.evaluate_js("document.getElementById('resetAll').disabled"))
                assert api._store.read()["theme"] == "#4fd8ff" and window.native.TopMost
                api._store.write = original_write
                js("document.getElementById('resetAll').click(); return true;")
                wait_until(lambda: (api._store.read() or {}).get("theme") == "#a78bfa")
                wait_until(lambda: not window.evaluate_js("document.getElementById('resetAll').disabled"))
                after_reset = js("const settings=await import('./js/settings.js');"
                                 "return {theme:settings.store.theme,kept:JSON.stringify([settings.store.notes,"
                                 "settings.store.skills,settings.store.routines,settings.store.prof,settings.store.devs,settings.store.conn])};")
                assert after_reset["theme"] == "#a78bfa" and after_reset["kept"] == before_reset, (after_reset, before_reset)
                assert not window.native.TopMost
                outcome.update(reset_preserved_collections_profile=True, reset_failure_preserved_preferences=True)
            outcome.update(ok=True, phase=phase, native=initial)
            if phase == "save":
                # Native restart gerçekten pencere/core'u kapatır. Yeni süreç
                # oluşturmayı yakalarız; ardıl gerçek süreci testin ana süreci açar.
                def launch(command, **kwargs):
                    assert not api._core._worker.is_alive()
                    launches.append(command)

                subprocess.Popen = launch
                window.run_js("document.getElementById('restartApp').click()")
                assert window.events.closed.wait(10), "Restart did not close the native window"
                outcome["native_restart_closed"] = True
            else:
                # Gerçek Shutdown düğmesi pencereyi yok etmeli; Restart ekranı
                # gösterilip açık kalan süreç bu beklemeyi geçemez.
                window.run_js("document.getElementById('shut').click()")
                assert window.events.closed.wait(10), "Shutdown did not close the native window"
                outcome["native_shutdown"] = True
        except Exception as error:
            outcome.update(ok=False, phase=phase, error=repr(error), trace=traceback.format_exc())
            outcome['wake_state'] = {'sleeping':api._sleeping, 'pending_hit':api._wake_detected,
                                     'sequence':getattr(api._wake,'_sequence',None)}
            outcome["diagnostic"] = window.evaluate_js("({shutdownErrors:window.shutdownErrors,model:document.getElementById('mSel')?.value,live:document.getElementById('liveLatencyTest')?.checked,mic:document.getElementById('micB')?.getAttribute('aria-pressed'),sendDisabled:document.getElementById('send')?.disabled,text:document.getElementById('textStatus')?.textContent,notes:document.getElementById('notesStatus')?.textContent,log:document.getElementById('log')?.textContent,ready:!!window.vex,bridge:typeof window.pywebview?.api?.event})")
            outcome["notes_file"] = (home / "notes.json").read_text("utf-8") if (home / "notes.json").exists() else None
        finally:
            (home / f"report-{phase}.json").write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
            if not window.events.closed.is_set():
                window.destroy()

    def start(**kwargs):
        original_start(func=exercise, **kwargs)

    webview.create_window, webview.start = create, start
    sys.argv = ["taskvex-native-smoke", *(["--debug"] if debug else [])]
    main()
    faulthandler.cancel_dump_traceback_later()
    if phase == "save":
        assert launches == [[sys.executable, "-m", "app.main"]], launches
        outcome["restart_launch_requested"] = True
        (home / f"report-{phase}.json").write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
    assert outcome.get("ok"), outcome


def run() -> None:
    """İki ayrı native süreci sınırla; sonucu isteğe bağlı rapora da yaz."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    parser.add_argument("--phase", choices=["save", "reopen", "notes", "persistence", "export_cancel", "credentials", "chat", "corrupt", "schema_invalid", "future"])
    parser.add_argument("--home", type=Path)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.phase:
        child(args.home, args.phase, args.debug)
        return
    reports = []
    with tempfile.TemporaryDirectory(prefix="taskvex-native-", ignore_cleanup_errors=True) as directory:
        home = Path(directory)
        for phase in ["save", "reopen", "notes", "persistence", "export_cancel", "credentials", "chat", "corrupt", "schema_invalid", "future"]:
            if phase == "corrupt":
                (home / "settings.json").write_bytes(b'{broken native settings')
            elif phase == "schema_invalid":
                (home / "settings.json").write_text(json.dumps({"version": 1, "data": {
                    "theme": "#4fd8ff", "vol": 9, "prof": {"pIns": "Native profile 📝"}}}), encoding="utf-8")
            elif phase == "future":
                (home / "settings.json").write_bytes(b'{"version":2,"data":{"future":true}}')
            # Windows venv launcher ikinci bir Python süreci yaratır. run()'ın
            # yalnız launcher'ı öldürmesi pipe'ı açık bırakabilir; kendi test
            # ağacımızı timeout'ta birlikte kapatıp hata kaydını dosyadan okuruz.
            log = home / f"{phase}.log"
            phase_home = home / "chat-profile" if phase == "chat" else home
            with log.open("wb") as output:
                process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--phase", phase,
                                            "--home", str(phase_home)], stdout=output, stderr=subprocess.STDOUT)
                try:
                    code = process.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   capture_output=True, timeout=15)
                    process.wait(timeout=10)
                    raise RuntimeError("Native test timed out:\n" + log.read_text("utf-8", errors="replace")[-5000:])
            path = phase_home / f"report-{phase}.json"
            report = json.loads(path.read_text("utf-8")) if path.exists() else {"ok": False, "phase": phase}
            reports.append(report)
            if code != 0 or not report.get("ok"):
                raise RuntimeError(f"{report}\n{log.read_text('utf-8', errors='replace')[-3500:]}")
    result = {"ok": True, "renderer": "edgechromium", "hidden_window": True, "phases": reports}
    if args.report:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    # Windows konsolu UTF-8 olmayabilir; rapor dosyası UTF-8, konsol ASCII-safe.
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    run()
