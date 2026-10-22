"""Not hedefini gerçek SDK/core ile, sentetik taşıma ve geçici dosyada seç.

Model yanlış ID önerse bile yalnız kullanıcının filtresine uyan tek gerçek
kayda izin verilir. Çoklu eşleşme, bozuk filtre ve belirsiz zaman yazı yapmaz.
Saatler kontrollü yedek restore ile sabittir; testler duvar saatinde beklemez.
"""

import pytest

from app.bootstrap import create_core
from app.session.model_tools import NoteTargetError
from app.session.text_chat import TextChat
from test_note_timestamps import confirmed
from test_local_tools import request
from test_model_note_mutations import execute, gateway, read
from test_gemini import transport
from test_live_probe import socket, frame
from test_live_tools import call as live_call, notes
from test_live_resume import wire, checkpoint, GOAWAY


def records(core, *, second_text="Başka not", second_time: str | None = "2024-01-01T00:00:00.000Z"):
    """En yeni kayıt özellikle ilk sıradadır: konumdan hedef seçilmemeli."""
    items = [{"id": "new-real-id", "text": "Merhaba dünya", "done": False,
              "created_at": "2025-02-01T00:00:00.000Z"},
             {"id": "old-real-id", "text": second_text, "done": False, "created_at": second_time}]
    confirmed(core, request("notes.replace", "seed-selection", {"notes": items}))
    return items


@pytest.mark.parametrize("mode", ["rest", "live"])
@pytest.mark.parametrize("prompt", ["İçinde 'merh' geçen notu sil", 'İÇİNDE “MERH” GEÇEN NOTU SİL',
    "'merh' içeren notu sil", 'Delete the note containing "merh"', "Son notu sil",
    "En son eklediğim notu sil", "Delete my latest note", "Delete the newest created note"])
def test_unique_partial_or_latest_selects_real_record(mode, prompt, transport, socket, taskvex_home):
    with create_core() as core:
        items = records(core)
        chat = TextChat(core)
        try:
            report = execute(chat, mode, prompt, [("notes.list", {}, "list"),
                ("notes.delete", {"id": items[0]["id"]}, "delete")], transport, socket)
            assert report["ok"] and notes(taskvex_home) == [items[1]]
            assert report["tool_results"][-1]["result"]["verified"]
        finally:
            assert chat.close()


@pytest.mark.parametrize("mode", ["rest", "live"])
@pytest.mark.parametrize("selector", ["partial", "latest"])
@pytest.mark.parametrize("change", [{"done": True}, {"text": "Edited safely"}])
def test_new_selectors_also_edit_or_complete_without_changing_metadata(mode, selector, change, transport, socket, taskvex_home):
    with create_core() as core:
        items = records(core)
        prompt = "İçinde 'merh' geçen notu değiştir" if selector == "partial" else "Son notu değiştir"
        chat = TextChat(core)
        try:
            report = execute(chat, mode, prompt, [("notes.list", {}, "read"),
                ("notes.update", {"id": items[0]["id"], **change}, "update")], transport, socket)
            assert report["ok"] and notes(taskvex_home) == [{**items[0], **change}, items[1]]
        finally:
            assert chat.close()


@pytest.mark.parametrize("mode", ["rest", "live"])
@pytest.mark.parametrize("reason", ["multiple", "wrong_id", "missing_date", "tied_date", "empty_query",
    "no_match", "two_queries", "combined", "unquoted", "negative_tr", "negative_en", "no_list"])
def test_unclear_or_wrong_selection_preserves_file(mode, reason, transport, socket, taskvex_home):
    with create_core() as core:
        items = records(core, second_text="Merhaba yine" if reason == "multiple" else "Başka not",
                        second_time=None if reason == "missing_date" else
                        "2025-02-01T00:00:00.000Z" if reason == "tied_date" else "2024-01-01T00:00:00.000Z")
        prompts = {"missing_date": "Son notu sil", "tied_date": "Son notu sil",
            "empty_query": "İçinde '' geçen notu sil", "no_match": "İçinde 'xyz' geçen notu sil",
            "two_queries": "İçinde 'merh' geçen notu ve içinde 'başka' geçen notu sil",
            "combined": "İçinde 'merh' geçen son notu sil", "unquoted": "İçinde merh geçen notu sil",
            "negative_tr": "İçinde 'merh' geçmeyen notu sil", "negative_en": "Delete a note not containing 'merh'"}
        prompt = prompts.get(reason, "İçinde 'merh' geçen notu sil")
        before = (taskvex_home / "notes.json").read_bytes()
        calls = [] if reason == "no_list" else [("notes.list", {}, "read")]
        target = items[1] if reason == "wrong_id" else items[0]
        chat = TextChat(core)
        try:
            report = execute(chat, mode, prompt, [*calls,
                ("notes.delete", {"id": target["id"]}, "delete")], transport, socket)
            assert not report["ok"] and report["code"] == "note_target_required"
            assert not report.get("unknown") and "Hangi notu" in report["error"]
            assert (taskvex_home / "notes.json").read_bytes() == before
        finally:
            assert chat.close()


def test_old_undated_record_also_prevents_latest_selection():
    with create_core() as core:
        confirmed(core, request("notes.replace", "legacy", {"notes": [
            {"id": "old", "text": "Undated", "done": False},
            {"id": "new", "text": "Dated", "done": False, "created_at": "2025-01-01T00:00:00.000Z"}]}))
        tools = gateway(core)
        tools.begin_turn("Son notu sil")
        read(tools)
        with pytest.raises(NoteTargetError):
            tools.submit({"id": "delete", "name": "notes.delete", "arguments": {"id": "new"}})


def test_explicit_id_disambiguates_contains_and_unknown_time():
    with create_core() as core:
        items = records(core, second_text="Merhaba yine", second_time=None)
        tools = gateway(core)
        tools.begin_turn(f"İçinde 'merh' geçen notlardan ID {items[1]['id']} olanı sil")
        read(tools)
        task = tools.submit({"id": "delete", "name": "notes.delete", "arguments": {"id": items[1]["id"]}})
        assert tools.result(task.task_id, timeout=2)["result"]["verified"]


def test_quoted_literal_note_name_is_not_latest_instruction(taskvex_home):
    with create_core() as core:
        items = records(core, second_text="son notu")
        tools = gateway(core)
        tools.begin_turn('"son notu" adlı notu sil')
        read(tools)
        task = tools.submit({"id": "delete", "name": "notes.delete", "arguments": {"id": items[1]["id"]}})
        assert tools.result(task.task_id, timeout=2)["result"]["verified"]
        assert notes(taskvex_home) == [items[0]]


def test_exact_short_note_cannot_bypass_ambiguous_contains_filter(taskvex_home):
    with create_core() as core:
        items = records(core, second_text="merh")
        tools = gateway(core)
        tools.begin_turn("İçinde 'merh' geçen notu sil")
        read(tools)
        with pytest.raises(NoteTargetError):
            tools.submit({"id": "delete", "name": "notes.delete", "arguments": {"id": items[1]["id"]}})
        assert notes(taskvex_home) == items


def test_partial_mutation_replay_and_next_turn_requires_fresh_list(wire, taskvex_home):
    with create_core() as core:
        items = records(core)
        delete = live_call("notes.delete", {"id": items[0]["id"]}, "same-delete")
        wire.plans = [{"turns": [[live_call("notes.list", {}, "list"), delete, frame("Deleted", complete=True)]],
                       "idle": [[checkpoint(), GOAWAY]]},
                      {"turns": [[delete, frame("Same result", complete=True)],
                                 [live_call("notes.delete", {"id": items[1]["id"]}, "new-delete")]]}]
        chat = TextChat(core)
        try:
            first = chat.run_live("İçinde 'merh' geçen notu sil", "future-live", notes_ready=True)
            second = chat.run_live("Replay", "future-live", notes_ready=True)
            third = chat.run_live("Son notu sil", "future-live", notes_ready=True)
            assert first["ok"] and second["ok"] and second["session_resumed"]
            assert first["tool_results"][-1]["task_id"] == second["tool_results"][0]["task_id"]
            assert not third["ok"] and third["code"] == "note_target_required"
            assert notes(taskvex_home) == [items[1]]
        finally:
            assert chat.close() and wire.opened == wire.closed
