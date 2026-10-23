"""Toplu not silmede seçim kapsamı, tek yazı, iptal ve belirsiz sonucu doğrular.

Gerçek core/JSON store kullanılır; REST/Live sağlayıcıları sentetiktir. Notlar
geçici test deposundadır; gerçek kullanıcı verisi veya ücretli API kullanılmaz.
"""
from threading import Event

import pytest

from app.bootstrap import create_core
from app.core.contracts import ContractError, ToolContext, TaskStatus
from app.session.model_tools import NoteTargetError
from app.session.text_chat import TextChat
from app.storage.json_store import JsonStore, StoreError
from app.tools.local.notes import NotesTools
from test_note_selection import records, selection
from test_model_note_mutations import gateway, current_snapshot, execute, seed
from test_note_timestamps import confirmed
from test_local_tools import request, run
from test_gemini import transport
from test_live_probe import socket
from test_live_tools import notes


@pytest.mark.parametrize('mode', ['rest', 'live'])
@pytest.mark.parametrize('selector', [
    {'kind': 'all', 'cardinality': 'many'},
    {'kind': 'latest', 'count': 2, 'cardinality': 'many'},
    {'kind': 'contains', 'text': 'not', 'cardinality': 'many'},
    {'kind': 'ids', 'ids': ['new-real-id', 'old-real-id'], 'cardinality': 'many'},
])
def test_model_deletes_exact_group_in_one_verified_write(mode, selector, transport, socket, taskvex_home, monkeypatch):
    with create_core() as core:
        items = records(core)
        writes = []
        original_write = JsonStore.write
        def write(store, data):
            writes.append(store.path)
            original_write(store, data)
        monkeypatch.setattr(JsonStore, 'write', write)
        # contains seçimi yalnız metninde "not" geçen eski notu hedefler.
        ids = [items[1]['id']] if selector['kind'] == 'contains' else [n['id'] for n in items]
        chat = TextChat(core)
        try:
            report = execute(chat, mode, 'Explicit request for this group', [('notes.select', selector, 'select'),
                ('notes.delete_many', {'ids': ids}, 'delete-group')], transport, socket)
            assert report['ok'] and len(writes) == 1
            final = report['tool_results'][-1]['result']
            assert final['verified'] and final['data']['deleted_count'] == len(ids)
            assert set(final['data']['deleted_ids']) == set(ids)
            assert notes(taskvex_home) == [n for n in items if n['id'] not in ids]
            saved = JsonStore(taskvex_home/'notes.json').read()
            assert saved is not None and saved['ui_migrated'] is True
        finally:
            assert chat.close()


@pytest.mark.parametrize('bad_ids', [['new-real-id'], ['new-real-id', 'old-real-id', 'extra'],
    ['new-real-id', 'new-real-id'], []])
def test_model_cannot_shrink_widen_or_duplicate_selected_group(bad_ids, taskvex_home):
    with create_core() as core:
        records(core); tools = gateway(core); tools.begin_turn('Delete all')
        selected = selection(tools, {'kind': 'all', 'cardinality': 'many'})['result']['data']
        before = (taskvex_home/'notes.json').read_bytes()
        with pytest.raises(ContractError):
            tools.submit({'id': 'wrong-group', 'name': 'notes.delete_many',
                'arguments': {'ids': bad_ids, 'expected_snapshot': selected['snapshot']}})
        assert (taskvex_home/'notes.json').read_bytes() == before


def test_single_selection_cannot_be_used_as_batch(taskvex_home):
    with create_core() as core:
        records(core); tools = gateway(core); tools.begin_turn('Delete one')
        selected = selection(tools, {'kind': 'latest', 'count': 1, 'cardinality': 'one'})['result']['data']
        with pytest.raises(NoteTargetError):
            tools.submit({'id': 'widen', 'name': 'notes.delete_many',
                'arguments': {'ids': ['new-real-id'], 'expected_snapshot': selected['snapshot']}})
        assert len(notes(taskvex_home)) == 2


def test_new_note_after_all_selection_prevents_every_deletion(taskvex_home):
    with create_core() as core:
        items = records(core); tools = gateway(core); tools.begin_turn('Delete all')
        selected = selection(tools, {'kind': 'all', 'cardinality': 'many'})['result']['data']
        seed(core, 'New UI note')
        before = (taskvex_home/'notes.json').read_bytes()
        task = tools.submit({'id': 'stale-all', 'name': 'notes.delete_many', 'arguments': {
            'ids': [n['id'] for n in items], 'expected_snapshot': selected['snapshot']}})
        result = tools.result(task.task_id, timeout=2)
        assert result['status'] == 'failed' and result['result']['error']['code'] == 'notes_changed'
        assert (taskvex_home/'notes.json').read_bytes() == before


def test_missing_id_in_core_batch_deletes_nothing(taskvex_home):
    with create_core() as core:
        records(core); before = (taskvex_home/'notes.json').read_bytes()
        result = run(core, request('notes.delete_many', 'missing', {
            'ids': ['new-real-id', 'missing'], 'expected_snapshot': current_snapshot()}))
        assert result.status == TaskStatus.FAILED and result.result is not None
        assert result.result.error is not None and result.result.error.code == 'not_found'
        assert (taskvex_home/'notes.json').read_bytes() == before


@pytest.mark.parametrize('boundary_tied', [True, False])
def test_latest_group_rejects_only_a_tie_crossing_the_boundary(boundary_tied):
    with create_core() as core:
        items = records(core)
        items[1]['created_at'] = items[0]['created_at']
        items.append({'id': 'third', 'text': 'Third', 'done': False,
            'created_at': items[0]['created_at'] if boundary_tied else '2023-01-01T00:00:00.000Z'})
        confirmed(core, request('notes.replace', 'ties', {'notes': items}))
        result = run(core, request('notes.select', 'select', {'kind': 'latest', 'count': 2, 'cardinality': 'many'}))
        assert (result.status == TaskStatus.FAILED) == boundary_tied
        if not boundary_tied:
            assert result.result is not None
            assert {n['id'] for n in result.result.data['notes']} == {'new-real-id', 'old-real-id'}


def test_replayed_batch_is_same_task_not_second_write(taskvex_home, monkeypatch):
    with create_core() as core:
        items = records(core); tools = gateway(core); tools.begin_turn('Delete all')
        selected = selection(tools, {'kind': 'all', 'cardinality': 'many'})['result']['data']
        call = {'id': 'batch', 'name': 'notes.delete_many', 'arguments': {
            'ids': [n['id'] for n in items], 'expected_snapshot': selected['snapshot']}}
        task = tools.submit(call); assert tools.result(task.task_id, timeout=2)['result']['verified']
        def forbidden(*args):
            pytest.fail('Replay must not write again')
        monkeypatch.setattr(JsonStore, 'write', forbidden)
        tools.begin_turn('Another turn')
        assert tools.submit(call).task_id == task.task_id
        assert tools.result(task.task_id)['result']['data']['deleted_count'] == 2
        assert notes(taskvex_home) == []


def test_batch_readback_failure_is_unknown_without_retry(taskvex_home, monkeypatch):
    with create_core() as core:
        items = records(core); snapshot = current_snapshot()
        original_write, original_read = JsonStore.write, JsonStore.read
        written = False
        def write(store, data):
            nonlocal written
            original_write(store, data); written = True
        def read(store):
            if written:
                raise StoreError('read_failed', 'Synthetic readback failure')
            return original_read(store)
        with monkeypatch.context() as patch:
            patch.setattr(JsonStore, 'write', write); patch.setattr(JsonStore, 'read', read)
            result = run(core, request('notes.delete_many', 'unknown', {
                'ids': [n['id'] for n in items], 'expected_snapshot': snapshot}))
        assert result.status == TaskStatus.UNKNOWN and result.result is not None and not result.result.verified
        assert notes(taskvex_home) == []


@pytest.mark.parametrize('cancel_before', [True, False])
def test_batch_stop_before_write_preserves_and_late_stop_keeps_real_result(taskvex_home, monkeypatch, cancel_before):
    with create_core() as core:
        items = records(core); snapshot = current_snapshot()
        args = {'ids': [n['id'] for n in items], 'expected_snapshot': snapshot}
        stopped = Event()
        if cancel_before:
            stopped.set()
        original_write = JsonStore.write
        def write(store, data):
            original_write(store, data); stopped.set()
        monkeypatch.setattr(JsonStore, 'write', write)
        result = NotesTools(JsonStore(taskvex_home/'notes.json')).delete_many(args,
            ToolContext(task_id='cancel-batch', request=request('notes.delete_many', 'cancel', args), cancel_event=stopped))
        assert result.status == (TaskStatus.CANCELLED if cancel_before else TaskStatus.SUCCEEDED)
        assert notes(taskvex_home) == (items if cancel_before else [])
