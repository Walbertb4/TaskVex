"""Uyku host kontrolü, yerel PCM sınırı ve Live'a ses sızmaması.

Gerçek sherpa ağırlığının SAPI deneyi ayrı rapordadır; pytest taşımayı sahte
algılayıcıyla denetler. Kullanıcı hesabı/sesi/notları veya ücretli API yoktur.
"""
from base64 import b64encode
from types import SimpleNamespace
from pathlib import Path

import pytest

from app.session.sleep_intent import wants_sleep
from app.session.text_chat import TextChat
from app.bootstrap import create_core
from app.session import wake_word
from test_native_bridge import bridge, ready
from test_live_probe import socket, frame


@pytest.mark.parametrize('text,expected', [
    ('uyku moduna gir', 'once'),
    ('Vex, uyku moduna gir.', 'once'),
    ('Lütfen, uyku moduna gir.', 'once'),
    ('lütfen Vex uykuya dal', 'once'),
    ('UYKU   MODUNA\tGİR', 'once'),
    ('uykuya geç lütfen', 'once'),
    ('Please, enter sleep mode.', 'once'),
    ('Vex, switch to sleep mode please.', 'once'),
    ('Computer please go to sleep', 'once'),
    ('kalıcı olarak uyku moduna gir', 'persistent'),
    ('Vex kalıcı olarak uyku moduna gir', 'persistent'),
    ('KALICI OLARAK UYKU MODUNA GİR', 'persistent'),
    ('bundan sonra uyku moduna geç', 'persistent'),
    ('artık uyku modunda kal', 'persistent'),
    ('lütfen uyku modunda kal', 'persistent'),
    ('Please Vex stay in sleep mode', 'persistent'),
    ('return to sleep after every task please', 'persistent'),
    ('from now on stay in sleep mode', 'persistent'),
    ('permanently enter sleep mode', 'persistent'),
    ('kalıcı uyku modunu kapat', 'off'),
    ('otomatik geri uyumayı kapat lütfen', 'off'),
    ('PLEASE STOP RETURNING TO SLEEP', 'off'),
])
def test_sleep_intent_accepts_complete_tr_en_variants(text, expected):
    """Hitap zorunlu değildir; boşluk/nezaket kipin anlamını değiştirmez."""
    from app.session.sleep_intent import sleep_mode
    assert sleep_mode(text, 'Computer') == expected
    assert wants_sleep(text, 'Computer') == (expected == 'once')


@pytest.mark.parametrize('text', [
    'uyku moduna gir?', 'Vex uykuya dal?', 'sleep?',
    'uyku moduna girme', 'sakın uyku moduna girme', 'uyku moduna girmeyelim',
    'do not enter sleep mode', "don't go to sleep", 'please do not sleep',
    'uyku moduna gir ne demek', 'can you explain enter sleep mode',
    'kalıcı olarak uyku moduna gir ne demek?',
    '"uyku moduna gir"', '“uyku moduna gir”', "'go to sleep'", '`sleep`',
    'notuma uyku moduna gir yaz', 'say go to sleep',
    'uyku moduna gir ve not ekle', 'not ekle sonra uyku moduna gir',
    'sleep and delete my notes', 'stay in sleep mode after deleting my notes',
    'uyku moduna gir ya da girme', 'uyku moduna gir ama önce saati söyle',
    'Vex başka uygulamayı uyku moduna al', 'Windows uyku moduna gir',
])
def test_sleep_intent_rejects_questions_negations_quotes_and_extra_work(text):
    from app.session.sleep_intent import sleep_mode
    assert sleep_mode(text) is None


@pytest.mark.parametrize('text', ['Vex uyku moduna geç.', 'uyu', 'go to sleep', 'Vex, enter sleep mode',
    'Rex, uykuya dal.', 'Max, uyku moduna geç.', 'Vex uykuya dal', 'Veks, uykuya dal.'])
def test_explicit_sleep_phrase(text):
    assert wants_sleep(text)


@pytest.mark.parametrize('text', ['Uyku moduna geç ne demek?', '"uyku moduna geç"', 'uyu ve not ekle',
    'bundan sonra uyku modunda kal', 'sleep mode is useful'])
def test_quoted_ambiguous_or_persistent_mode_not_mistaken_for_one_time_sleep(text):
    assert not wants_sleep(text)


def test_custom_address_and_sleeping_color_contract():
    from app.bridge.settings import validate_settings
    assert wants_sleep('Computer, uykuya dal.', 'Computer')
    assert not wants_sleep('Max uyku moduna geç ne demek?')
    assert not wants_sleep('Veks uykuya dal ne demek?')
    assert not wants_sleep('Veks uykuya dal ve not ekle')
    assert validate_settings({'colors':{'sleeping':'#64748b'}})['colors']['sleeping']=='#64748b'


def test_typed_sleep_does_not_call_provider_and_keeps_memory():
    with create_core() as core:
        chat=TextChat(core)
        chat._memory.remember('Fact', {'ok':True,'text':'Understood'})
        report=chat.run_live('Vex uyku moduna geç', 'future-live')
        assert report['sleep_requested'] and report['completed'] and report['ok']
        assert chat._live._thread is None and chat._memory.snapshot()
        assert chat.close()


@pytest.mark.parametrize('text', ['Vex uyku moduna geç', 'Rex, uykuya dal.', 'Max, uyku moduna geç.', 'Veks, uykuya dal.'])
def test_voice_sleep_closes_live_without_starting_model_tool(socket, text):
    socket.frames=[{'setupComplete':{}}, {'serverContent':{'inputTranscription':{'text':text,'finished':True}}}]
    with create_core() as core:
        chat=TextChat(core)
        report=chat.run_live('', 'future-live', audio_input=bytes(3200))
        assert report['sleep_requested'] and report['ok'] and socket.closed
        assert not report['tool_results'] and chat._memory.snapshot()
        assert chat.close()


def test_partial_sleep_transcript_does_not_consume_a_question(socket):
    socket.frames=[{'setupComplete':{}},
        {'serverContent':{'inputTranscription':{'text':'uyku moduna geç'}}},
        {'serverContent':{'inputTranscription':{'text':' ne demek?','finished':True}}}, frame('Explanation',complete=True)]
    with create_core() as core:
        chat=TextChat(core)
        report=chat.run_live('', 'future-live', audio_input=bytes(3200))
        assert report['ok'] and not report.get('sleep_requested')
        assert chat.close()


def test_local_wake_gate_order_and_stale_packets(bridge, monkeypatch):
    assert ready(bridge)['ok']
    class Detector:
        id='synthetic-wake'
        def __init__(self, word): self.sequence=0
        def feed(self, seq, pcm):
            assert len(pcm)==3200 and seq==self.sequence
            self.sequence+=1
            return seq==1
    monkeypatch.setattr('app.bridge.webview_bridge.WakeWord',Detector)
    started=bridge.event('sleep_start')
    assert started['ok'] and bridge._sleeping
    assert bridge.event('live_audio_start',{'request_id':'blocked'})['code']=='sleeping'
    packet={'request_id':started['request_id'],'sequence':0,'data':b64encode(bytes(3200)).decode()}
    assert not bridge.event('wake_feed',packet)['detected']
    assert not bridge.event('wake_feed',{**packet,'request_id':'old'})['ok'] and bridge._sleeping
    assert bridge.event('wake_feed',{**packet,'sequence':1})['detected']
    assert bridge._sleeping and bridge._wake is not None
    assert bridge.event('live_audio_start',{'request_id':'still-blocked'})['code']=='sleeping'
    assert not bridge.event('wake',{'request_id':'old'})['ok']
    assert bridge.event('wake',{'request_id':started['request_id']})['completed']
    assert not bridge._sleeping and bridge._wake is None
    assert not bridge.event('wake_feed',packet)['ok']


def test_rejected_ui_prefix_keeps_host_asleep_and_revokes_pending_hit(bridge):
    assert ready(bridge)['ok']
    bridge._sleeping = True
    bridge._wake = SimpleNamespace(id='pending-hit')
    bridge._wake_detected = True
    assert bridge.event('wake_close','pending-hit')['completed']
    assert bridge._sleeping and bridge._wake is None
    assert not bridge.event('wake',{'request_id':'pending-hit'})['ok']


def test_missing_model_or_bad_packet_stays_asleep_manual_wake_recovers(bridge, monkeypatch):
    assert ready(bridge)['ok']
    def missing(word):raise FileNotFoundError('synthetic')
    monkeypatch.setattr('app.bridge.webview_bridge.WakeWord',missing)
    assert not bridge.event('sleep_start')['ok'] and bridge._sleeping
    assert bridge.event('live_audio_start',{'request_id':'blocked'})['code']=='sleeping'
    assert bridge.event('wake')['completed'] and not bridge._sleeping
    bridge._wake=SimpleNamespace(id='one',feed=lambda *args: (_ for _ in ()).throw(ValueError()))
    bridge._sleeping=True
    result=bridge.event('wake_feed',{'request_id':'one','sequence':0,'data':'bad'})
    assert not result['ok'] and bridge._sleeping and bridge._wake is None


@pytest.mark.parametrize('error,code', [(wake_word.WakeAlignmentError('private detail'),'wake_alignment_failed'),
    (ValueError('private detail'),'wake_packet_rejected'),(RuntimeError('private detail'),'wake_engine_failed')])
def test_wake_failure_codes_distinguish_alignment_packet_and_engine(bridge,error,code):
    assert ready(bridge)['ok']
    bridge._sleeping=True
    bridge._wake=SimpleNamespace(id='broken',feed=lambda *args: (_ for _ in ()).throw(error))
    result=bridge.event('wake_feed',{'request_id':'broken','sequence':0,'data':b64encode(bytes(3200)).decode()})
    assert result['code']==code and not result['ok'] and bridge._sleeping
    assert 'private detail' not in str(result) and bridge._wake is None


def test_model_setup_rejects_changed_archive_before_writing(monkeypatch, taskvex_home):
    from io import BytesIO
    monkeypatch.setattr('urllib.request.urlopen',lambda *a,**k:BytesIO(b'not the pinned archive'))
    with pytest.raises(ValueError,match='integrity'):
        wake_word.setup()
    assert not taskvex_home.exists()


def test_bad_word_and_missing_model_fail_before_native_kernel(monkeypatch,tmp_path):
    monkeypatch.setattr(wake_word,'model_home',lambda:tmp_path)
    with pytest.raises(ValueError):wake_word.WakeWord('../bad')
    with pytest.raises(FileNotFoundError):wake_word.WakeWord('Vex')


def test_pcm_sequence_endian_and_keyword_boundary(monkeypatch,tmp_path):
    import sherpa_onnx
    from hashlib import sha256
    files={'tokens.txt':b'V 0\nEH1 1\nK 2\nS 3','en.phone':b'VEX V EH1 K S'}
    for name,data in files.items():(tmp_path/name).write_bytes(data)
    monkeypatch.setattr(wake_word,'model_home',lambda:tmp_path)
    monkeypatch.setattr(wake_word,'FILES',{n:sha256(v).hexdigest() for n,v in files.items()})
    state=SimpleNamespace(ready=False,samples=[],hit=False)
    class Kernel:
        def __init__(self,**kwargs):
            assert 'V EH1 K S' in Path(kwargs['keywords_file']).read_text()
            self.keyword_spotter=self
        def create_stream(self):return self
        def accept_waveform(self,rate,samples):
            assert rate==16000
            state.samples=samples;state.ready=True
        def is_ready(self,s):return state.ready
        def decode_stream(self,s):state.ready=False
        def get_result(self,s):return SimpleNamespace(keyword='WAKE' if state.hit else '',timestamps=[0.1])
    monkeypatch.setattr(sherpa_onnx,'KeywordSpotter',Kernel)
    detector=wake_word.WakeWord('Vex')
    assert not list(tmp_path.glob('keyword-*'))
    with pytest.raises(ValueError):detector.feed(True,bytes(3200))
    assert not detector.feed(0,b'\x00\x80'*1600)
    assert state.samples[0]==-1
    state.hit=True
    assert detector.feed(1,bytes(3200)) and detector.start_sequence==1


@pytest.mark.parametrize('stamps,valid', [([.24,.48],True), ([float('nan')],False),
    ([.6,.2],False), ([1.6,1.8],False), ([],False)])
def test_boundary_verifies_fresh_window_instead_of_trusting_old_segment_time(stamps,valid,monkeypatch):
    from collections import deque
    detector = object.__new__(wake_word.WakeWord)
    detector._recent = deque([(seq,bytes(3200)) for seq in range(650,658)],maxlen=30)
    state = SimpleNamespace(ready=True)
    class Verification:
        def __init__(self):self.keyword_spotter=self
        def create_stream(self):return self
        def accept_waveform(self,rate,samples):
            assert rate==16000 and len(samples)==8*1600+4800
        def is_ready(self,s):return state.ready
        def decode_stream(self,s):state.ready=False
        def get_result(self,s):return SimpleNamespace(keyword='WAKE',timestamps=stamps)
    monkeypatch.setattr(detector,'_spotter',Verification(),raising=False)
    old=SimpleNamespace(keyword='WAKE',timestamps=[.4,.68])
    if valid:
        assert detector._boundary(old,657)==652
    else:
        with pytest.raises(ValueError):detector._boundary(old,657)


@pytest.mark.parametrize('phrase', ['Vex uykuya dal', 'uyku moduna gir',
    'kalıcı olarak uyku moduna gir', 'please switch to sleep mode'])
@pytest.mark.parametrize('finished_empty', [False, True])
def test_sleep_candidate_holds_denial_audio_until_host_decision(socket, finished_empty, phrase):
    """Bitmemiş tam adayın ret sesi oynatılmaz; bitiş host uyku sonucudur."""
    from app.session.live_probe import probe_live_text
    import asyncio
    socket.frames = [{'setupComplete': {}},
        {'serverContent': {'inputTranscription': {'text': phrase}}},
        frame('Main computer access needed.', audio=True),
        {'serverContent': {'inputTranscription': {'finished': True}}} if finished_empty else frame(complete=True)]
    audio, text = [], []
    report = asyncio.run(probe_live_text('', 'future-live', audio_input=bytes(3200),
        audio_sink=lambda *args: audio.append(args) or True,
        transcript_sink=lambda role, value, seq: text.append((role, value)) or True))
    assert report['ok'] and report['sleep_requested']
    assert report['text'] == 'Sleep mode requested.' and not audio
    assert all('Main computer' not in value for _, value in text)


@pytest.mark.parametrize('candidate,suffix', [
    ('uyku moduna geç', ' ne demek?'),
    ('uyku moduna gir', 'me'),
    ('kalıcı olarak uyku moduna gir', ' ne demek?'),
    ('please switch to sleep mode', ' and delete my notes')])
def test_sleep_candidate_becomes_question_releases_held_output_in_order(socket, candidate, suffix):
    """Aday soru olursa gerçek cevap kaybolmaz, uykuya geçilmez."""
    from app.session.live_probe import probe_live_text
    import asyncio
    socket.frames = [{'setupComplete': {}},
        {'serverContent': {'inputTranscription': {'text': candidate}}},
        frame('Sleep '),
        {'serverContent': {'inputTranscription': {'text': suffix, 'finished': True}}},
        frame('explained.', complete=True)]
    report = asyncio.run(probe_live_text('', 'future-live', audio_input=bytes(3200)))
    assert report['ok'] and not report.get('sleep_requested')
    assert report['text'] == 'Sleep explained.'


@pytest.mark.parametrize('text, expected', [
    ('Vex bundan sonra uyku modunda kal', 'persistent'),
    ('Veks, uyku modunda kal.', 'persistent'),
    ('Computer, stay in sleep mode', 'persistent'),
    ('Vex uyku modundan kalıcı olarak çık', 'off'),
    ('disable automatic sleep', 'off'),
    ('Vex uykuya dal', 'once'),
    ('uyku modunda kal ne demek?', None),
    ('uyku modunda kal ve not ekle', None),
    ('"stay in sleep mode"', None)])
def test_sleep_mode_is_explicit_and_not_a_question(text, expected):
    from app.session.sleep_intent import sleep_mode
    assert sleep_mode(text, 'Computer') == expected


@pytest.mark.parametrize('text, mode', [
    ('Vex bundan sonra uyku modunda kal', 'persistent'),
    ('Vex uyku modundan kalıcı olarak çık', 'off'),
    ('Lütfen, uyku moduna gir.', 'once'),
    ('Vex kalıcı olarak uyku moduna gir', 'persistent'),
    ('kalıcı uyku modunu kapat', 'off'),
    ('Computer please switch to sleep mode', 'once'),
    ('return to sleep after every task please', 'persistent'),
    ('please stop returning to sleep', 'off')])
def test_persistent_sleep_controls_work_typed_and_voice_without_tools(socket, text, mode):
    with create_core() as core:
        chat = TextChat(core)
        typed = chat.run_live(text, 'future-live', profile={'pWake':'Computer'})
        assert typed['ok'] and typed['sleep_mode'] == mode
        assert typed['sleep_requested'] == (mode != 'off') and not typed['model_attempts']
        socket.frames = [{'setupComplete': {}},
            {'serverContent': {'inputTranscription': {'text': text, 'finished': True}}}]
        voice = chat.run_live('', 'future-live', audio_input=bytes(3200), profile={'pWake':'Computer'})
        assert voice['ok'] and voice['sleep_mode'] == mode
        assert voice['sleep_requested'] == (mode != 'off') and not voice['tool_results']
        assert chat.close()


@pytest.mark.parametrize('value', [-1, 301, 1.5, '5', True])
def test_sleep_delay_rejects_invalid_persisted_values(value):
    from app.bridge.settings import validate_settings
    from app.core.contracts import ContractError
    with pytest.raises(ContractError):
        validate_settings({'sleepDelay': value})


def test_sleep_delay_saved_and_read_back_with_other_settings(bridge):
    assert ready(bridge)['ok']
    assert bridge.event('save', {'sleepDelay': 3})['ok']
    assert bridge._store.read()['sleepDelay'] == 3
    assert bridge.event('save', {'sleepDelay': 301})['ok'] is False
    assert bridge._store.read()['sleepDelay'] == 3


def test_zero_disables_idle_sleep_timer_without_changing_other_settings(bridge):
    assert ready(bridge)['ok']
    assert bridge.event('save', {'sleepDelay': 0})['ok']
    assert bridge._store.read()['sleepDelay'] == 0



def test_refused_sleep_reports_confirmed_awake_state(bridge, monkeypatch):
    assert ready(bridge)['ok']
    monkeypatch.setattr(bridge._chat, 'reset_live', lambda: False)
    result = bridge.event('sleep_start')
    assert result['ok'] is False and result['completed'] is True
    assert result['sleeping'] is False and not bridge._sleeping
    assert result['code'] == 'sleep_rejected'


def test_wake_model_is_reused_but_input_id_and_state_are_fresh(bridge, monkeypatch):
    """Pahalı ağırlık kurulumu bir kez; eski hit/PCM yeni uykuya taşınmaz."""
    from uuid import uuid4
    built = []
    class Detector:
        def __init__(self, word):
            built.append(word)
            self.restart()
        def restart(self):
            self.id = uuid4().hex
            self.sequence = 0
        def feed(self, sequence, pcm):
            assert sequence == self.sequence
            self.sequence += 1
            return False
    monkeypatch.setattr('app.bridge.webview_bridge.WakeWord', Detector)
    assert ready(bridge)['ok']
    first = bridge.event('sleep_start')
    assert bridge.event('wake_feed', {'request_id':first['request_id'], 'sequence':0,
        'data':b64encode(bytes(3200)).decode()})['ok']
    assert bridge.event('wake')['ok']
    second = bridge.event('sleep_start')
    assert second['request_id'] != first['request_id'] and len(built) == 1
    assert bridge._wake.sequence == 0
    assert not bridge.event('wake_feed', {'request_id':first['request_id'], 'sequence':1,
        'data':b64encode(bytes(3200)).decode()})['ok']
    assert bridge.event('wake')['ok']
    assert bridge.event('save', {'prof':{'pWake':'Computer'}})['ok']
    assert bridge.event('sleep_start')['ok'] and built == ['Vex', 'Computer']


def test_control_audio_assets_are_small_valid_pcm_waves():
    """Üretimle paketlenen sabit onay sesleri: kullanıcı sesi veya API yok."""
    import wave
    directory = Path(__file__).resolve().parents[1] / 'ui' / 'assets' / 'controls'
    for language in ('tr', 'en'):
        for mode in ('once', 'persistent', 'off'):
            with wave.open(str(directory / f'sleep-{mode}-{language}.wav')) as audio:
                assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, 24000)
                assert 0 < audio.getnframes() / 24000 < 8


def test_broken_wake_cleanup_cannot_prevent_explicit_wake(bridge):
    assert ready(bridge)['ok']
    def broken_restart():
        raise RuntimeError('Synthetic decoder cleanup failure')
    detector = SimpleNamespace(id='broken-input', restart=broken_restart)
    bridge._sleeping = True
    bridge._wake = detector
    bridge._wake_cached = ('Vex', detector)
    assert bridge.event('wake')['completed']
    assert not bridge._sleeping and bridge._wake is None and bridge._wake_cached is None
