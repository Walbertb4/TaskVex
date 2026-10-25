"""REST TTS and Stop: real SDK, temps and synthetic only HTTP/PCM.

The audio error does not corrupt the completed text/tool result; no real account
physical device is not tested. Native testing further validates UI delivery.
"""
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import httpx
import pytest

from app.bootstrap import create_core
from app.session.gemini import DEFAULT_MODEL
from app.session.speech import GeminiSpeech, SPEECH_MODEL
from app.session.text_chat import TextChat
from test_gemini import transport, reply, call, stored_notes


def audio(data=bytes(480), **fields):
    """Give limited mono PCM response to Interactions parser."""
    return {'id':'test-tts', 'status':'completed', 'steps':[{'type':'model_output',
        'content':[{'type':'audio', 'mime_type':'audio/l16', 'sample_rate':24000,
                    'data':b64encode(data).decode(), **fields}]}]}


def test_reply_read_once_without_tools_and_preserved_mutation(transport, taskvex_home):
    transport.responses = [reply([call()]), reply([{'text':'Add a notendi.'}]), audio()]
    delivered = []
    with create_core() as core:
        chat = TextChat(core, audio_sink=lambda *args: delivered.append(args) or True)
        report = chat.run('Add note', DEFAULT_MODEL, request_id='rest-1')
        assert report['ok'] and len(transport.requests) == 2 and not delivered
        assert chat.read_reply('wrong')['audio_error'] == 'speech_not_pending'
        spoken = chat.read_reply('rest-1')
        assert spoken['ok'] and spoken['audio_bytes_forwarded'] == 480
        assert delivered == [('rest-1', bytes(480), 'audio/pcm;rate=24000')]
        assert len(stored_notes(taskvex_home)) == 1
        assert chat.read_reply('rest-1')['audio_error'] == 'speech_not_pending'
        assert len(transport.requests) == 3
        body = transport.requests[-1]
        assert body['model'] == SPEECH_MODEL and body['store'] is False
        assert body['input'][0]['content'][0]['text'] == 'Add a notendi.'
        assert 'tools' not in body and body['response_format']['sample_rate'] == 24000
        assert chat.close()


@pytest.mark.parametrize('ending', [httpx.Response(503, json={'error':{'message':'SECRET'}}),
    audio(b'x'), audio(sample_rate=16000), audio(mime_type='audio/mp3'), audio(channels=2)])
def test_speech_failure_preserves_text_without_retry(transport, ending):
    transport.responses = [reply([{'text':'Keep answer'}]), ending]
    with create_core() as core:
        chat = TextChat(core, audio_sink=lambda *args: True)
        report = chat.run('Hi', DEFAULT_MODEL, request_id='first')
        speech = chat.read_reply('first')
        assert report['ok'] and report['text'] == 'Keep answer'
        assert not speech['ok'] and speech['completed'] and speech['audio_error']
        assert 'SECRET' not in str(speech) and len(transport.requests) == 2
        assert transport.options[-1].retry_options.attempts == 0
        assert chat.close()


def test_pending_reply_stop_and_stale_id(transport):
    transport.responses = [reply([{'text':'First'}]), reply([{'text':'Second'}]), audio()]
    with create_core() as core:
        chat = TextChat(core, audio_sink=lambda *args: True)
        chat.run('Hi', DEFAULT_MODEL, request_id='old')
        assert chat.stop('old')['accepted']
        assert chat.read_reply('old')['audio_error'] == 'speech_not_pending'
        chat.run('Hi again', DEFAULT_MODEL, request_id='new')
        assert not chat.stop('old')['ok']
        assert chat.read_reply('old')['audio_error'] == 'speech_not_pending'
        assert chat.read_reply('new')['ok']
        assert chat.close()


def test_speech_stop_during_http_waits_for_completion(transport):
    started, release = Event(), Event()
    def blocked(request):
        started.set()
        assert release.wait(5)
        return httpx.Response(200, json=audio())
    transport.responses = [reply([{'text':'Keep answer'}]), blocked]
    delivered = []
    with create_core() as core, ThreadPoolExecutor() as executor:
        chat = TextChat(core, audio_sink=lambda *args: delivered.append(args) or True)
        chat.run('Hi', DEFAULT_MODEL, request_id='current')
        future = executor.submit(chat.read_reply, 'current')
        try:
            assert started.wait(5)
            stop = chat.stop('current')
            assert stop['accepted'] and not stop['completed'] and stop['waiting_for'] == 'speech_response'
            assert chat.busy and not future.done() and not chat.close()
            assert not chat.stop('old')['ok']
        finally:
            release.set()
        result = future.result(5)
        assert result['stopped'] and result['completed'] and not delivered
        assert len(transport.requests) == 2 and chat.close()


def test_speech_stop_before_http_and_during_delivery(transport):
    speech = GeminiSpeech()
    speech.stop()
    assert speech.run('Hi', lambda *args: True)['stopped']
    assert not transport.requests
    transport.responses = [audio(bytes(96000))]
    speech = GeminiSpeech()
    delivered = []
    def sink(data, mime):
        delivered.append(data)
        speech.stop()
        return True
    result = speech.run('Hi', sink)
    assert result['stopped'] and len(delivered) == 1 and len(transport.requests) == 1



def test_speech_usage_joins_same_application_total_once(transport):
    message=reply([{'text':'Hello'}]);message['usageMetadata']={'totalTokenCount':12}
    spoken=audio();spoken['usage']={'total_tokens':8}
    transport.responses=[message,spoken]
    with create_core() as core:
        chat=TextChat(core,audio_sink=lambda *args:True)
        try:
            assert chat.run('Hi',DEFAULT_MODEL,request_id='tts')['usage_tokens']==12
            report=chat.read_reply('tts')
            assert report['ok'] and report['usage_tokens']==20 and not report['usage_partial']
            assert not chat.read_reply('tts')['ok']
            assert chat._usage.report({})['usage_tokens']==20
        finally:
            assert chat.close()
