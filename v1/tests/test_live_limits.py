"""Live olay sessizliği ile toplam süreyi hızlı sentetik zamanlarla ayırır.

Gerçek SDK/socket fixture'ı kullanılır; saniyeler yalnız bu testlerde küçültülür.
Timeout hiçbir mesajı/yan etkiyi tekrar etmez; geçerli araç kanıtını korur.
"""
import asyncio

from app.bootstrap import create_core
from app.session import live_probe
from app.session.live_session import PersistentLive
from app.session.live_input import LiveInput
from test_live_probe import socket, frame
from test_live_tools import tools, call, notes


def test_idle_timeout_preserves_completed_note_and_does_not_retry(socket, monkeypatch, taskvex_home):
    monkeypatch.setattr(live_probe,'LIVE_IDLE_SECONDS',.02)
    socket.frames=[{'setupComplete':{}},call()]
    socket.stall=True
    with create_core() as core:
        report=asyncio.run(live_probe.probe_live_text('Add','future-live',tools=tools(core)))
    assert report['code']=='live_idle_timeout' and report['timeout_seconds']==.02
    assert socket.opened==1 and socket.closed and len(notes(taskvex_home))==1
    assert report['tool_results'][0]['result']['verified'] and not report.get('unknown')


def test_events_can_continue_past_idle_duration_but_total_limit_still_applies(socket, monkeypatch):
    monkeypatch.setattr(live_probe,'LIVE_IDLE_SECONDS',.08)
    monkeypatch.setattr(live_probe,'LIVE_TURN_SECONDS',.5)
    original=live_probe._next_message
    async def slowly(*args):
        await asyncio.sleep(.02)
        return await original(*args)
    monkeypatch.setattr(live_probe,'_next_message',slowly)
    socket.frames=[{'setupComplete':{}},*[frame('Word ') for _ in range(6)],frame('Done',complete=True)]
    first=asyncio.run(live_probe.probe_live_text('Hello','future-live'))
    assert first['ok'] and first['elapsed_ms']>80 and first['text'].endswith('Done')
    monkeypatch.setattr(live_probe,'LIVE_TURN_SECONDS',.06)
    socket.frames=[{'setupComplete':{}},*[frame('Word ') for _ in range(20)]]
    second=asyncio.run(live_probe.probe_live_text('Hello again','future-live'))
    assert second['code']=='live_timeout' and second['timeout_seconds']==.06
    assert second['text'] and socket.opened==2 and socket.closed


def test_feed_distinguishes_normal_close_from_invalid_input():
    host=PersistentLive()
    assert host.input('old',0,bytes(3200))=={'ok':False,'closed':True,'failed':False}
    # Yalnız kuyruk sözleşmesini dene; I/O thread veya API açılmaz.
    from threading import Event
    host._pending=('current',Event())
    host._input=LiveInput();host._input.ready=True
    assert host.input('current',0,bytes(3200))['ok']
    invalid=host.input('current',0,bytes(3200))
    assert not invalid['ok'] and invalid['closed'] and invalid['failed']
    host._pending=host._input=None
