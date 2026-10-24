"""Native kabul senaryolarının gerçek UI/core assertion’ları.

Süreç/HTTP/WebSocket kurulumunu native_smoke.py yapar. Buradaki fonksiyonlar
kendilerine verilen pencere, köprü ve sentetik taşıma ile davranışı doğrular;
gerçek API hesabı veya kullanıcı kaydı kullanmaz.
"""
import json
import os
from pathlib import Path
import time

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
        js("document.getElementById('tabTmB').click();document.querySelector('#clockList button[data-clock-id=\""+timer['id']+"\"]').click();document.getElementById('tmMin').value='4';document.getElementById('tmSec').value='5';document.getElementById('tmSetB').click();return true;")
        wait_until(lambda: next(c for c in api._clocks.snapshot()['clocks'] if c['id']==timer['id'])['duration_seconds']==245)
        wait_until(lambda: not window.evaluate_js("document.getElementById('tmSetB').disabled"))
        assert next(c for c in api._clocks.snapshot()['clocks'] if c['id']==timer['id'])['state']=='ready'
        outcome[mode+'_timer_set_preserved_selected_id']=True
        outcome[mode+'_multi_clocks_same_ids_ui_controls_and_automatic_tabs']=True
    assert len(api._clocks.snapshot()['clocks'])==6
    # Gerçek WebView CSS'si tema değişimini izlemeli; profil/veri yazılmaz.
    assert js("const root=document.documentElement,s=document.getElementById('clockSelect'),old=root.style.getPropertyValue('--gold');try{root.style.setProperty('--gold','#12ab34');const a=getComputedStyle(s).color;root.style.setProperty('--gold','#ab3412');return a==='rgb(18, 171, 52)'&&getComputedStyle(s).color==='rgb(171, 52, 18)'&&getComputedStyle(s).appearance==='none'&&getComputedStyle(s).backgroundColor!=='rgb(255, 255, 255)'&&s.getBoundingClientRect().width<=s.closest('.tmin').getBoundingClientRect().width;}finally{if(old)root.style.setProperty('--gold',old);else root.style.removeProperty('--gold');}")
    outcome['clock_selector_webview_theme_and_width']=True
    # UI aksanları --c (reaktör) değişiminden etkilenmemeli, --gold'u izlemeli.
    assert js("const root=document.documentElement,old=root.style.getPropertyValue('--c'),r=document.getElementById('wakeR'),a=document.getElementById('inputArrow');try{root.style.setProperty('--c','#ff6600');const first=[getComputedStyle(r).backgroundColor,getComputedStyle(r,'::-webkit-slider-thumb').backgroundColor,getComputedStyle(a).color];root.style.setProperty('--c','#00ff00');return JSON.stringify(first)===JSON.stringify([getComputedStyle(r).backgroundColor,getComputedStyle(r,'::-webkit-slider-thumb').backgroundColor,getComputedStyle(a).color])&&getComputedStyle(a).color===getComputedStyle(document.getElementById('clockSelect')).color;}finally{if(old)root.style.setProperty('--c',old);else root.style.removeProperty('--c');}")
    outcome['sliders_and_input_arrow_ignore_reactor_state_color']=True
    assert js("const picker=document.getElementById('clockPicker'),head=document.getElementById('clockSelect');head.focus();head.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowUp',bubbles:true,cancelable:true}));return picker.open&&document.activeElement===document.getElementById('clockList').lastElementChild;")
    js("window.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));return true;")
    assert js("return !document.getElementById('clockPicker').open&&document.activeElement===document.getElementById('clockSelect');")
    outcome['clock_picker_keyboard_and_escape']=True

    # Açık HTML listesinde sağ tık, seçili kayıt yerine sağ tıklanan ID'yi siler.
    for kind,tab in [('timer','tabTmB'),('stopwatch','tabSwB')]:
        records=[c for c in api._clocks.snapshot()['clocks'] if c['kind']==kind]
        target=records[-1]['id'];keep=records[0]['id']
        js("document.getElementById('"+tab+"').click();document.querySelector('#clockList button[data-clock-id=\""+keep+"\"]').click();document.getElementById('clockPicker').open=true;document.querySelector('#clockList button[data-clock-id=\""+target+"\"]').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:100,clientY:150}));return true;")
        assert window.evaluate_js("!document.getElementById('clockMenu').hidden")
        assert window.evaluate_js("document.getElementById('clockSelect').value")==keep
        js("document.getElementById('clockDelete').click();return true;")
        wait_until(lambda:not any(c['id']==target for c in api._clocks.snapshot()['clocks']))
        wait_until(lambda:not window.evaluate_js("document.getElementById('clockNew').disabled"))
        assert any(c['id']==keep for c in api._clocks.snapshot()['clocks'])
        outcome[kind+'_right_click_deleted_only_target']=True
    # Son stopwatch silindiğinde boş görünüm ve yeniden oluşturabilme korunur.
    last=next(c for c in api._clocks.snapshot()['clocks'] if c['kind']=='stopwatch')['id']
    js("document.getElementById('clockPicker').open=true;document.querySelector('#clockList button[data-clock-id=\""+last+"\"]').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:100,clientY:150}));document.getElementById('clockDelete').click();return true;")
    wait_until(lambda:not any(c['kind']=='stopwatch' for c in api._clocks.snapshot()['clocks']))
    wait_until(lambda:window.evaluate_js("document.getElementById('clockSelect').textContent")== 'No stopwatch yet')
    assert window.evaluate_js("document.getElementById('tm').textContent")=='00:00'
    outcome['last_clock_delete_empty_state']=True

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
    previous_wake_replies = window.evaluate_js("document.getElementById('msgs').textContent").count('Native microphone answer')
    wake_state['detect'] = True
    js("wakeOsc.connect(wakeDestinations.at(-1));return true;")
    wait_until(lambda: not api._sleeping and window.evaluate_js("document.getElementById('msgs').textContent").count('Native microphone answer') > previous_wake_replies)
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


