# Stage 3 — Transfer of notes to backend

This document describes not CRUD migration. CRUD; insert, read, update and delete.
In native app, permanent owner Python/backend is native UI in browser-only mode.

## Progress — October 21, 2026

| Step | Status |
|---|---|
| CRUD with fixed ID in Core; registry/policy/tests | Completed |
| Native events, final result and UI ID mapping | Completed |
| Approved old grade transfer; backend authority on reopening | Completed |
| Loading Old/new note backup via core and exporting with ID | Completed |
| Automatically accept browser native mode and real WebView2 | Completed |
| Acceptance with visible window and real file dialog | Completed with Computer Use; [observed results](STAGE3_VISIBLE_ACCEPTANCE.md) |

## Use and ownership

At the first native startup, notes are read-only. `Use backend notes` button
Requests transfer confirmation. On cancellation, the file is not written and old local notes are preserved. On approval
UI notes are added with separate IDs while preserving the old core notes. with the same text
two notes are not combined; completion states are carried over. Empty list is also open confirm
Can be transferred to backend ownership. If there is a sign, the next opening will be connected automatically.

`notes.json` envelope version=1, data format `{notes:[{id,text,done,created_at?}],ui_migrated:true}`.
The old not-only-listed core file is still read. `ui_migrated` same as notes
atomic is written in replace; There is no separate flag file. If the last note is deleted
The sign is also protected. So delayed response, crash or reopening will restore the old list.
does not add it a second time. localStorage is the new data authority with backend checked
does not count; It is the view/backup cache. Corrupt existing storage is not automatically reset.

During the note action, the relevant controls are closed. UI validated list only
replaces it with the backend result. In case of rejection, the insertion text is preserved. Response in 12 seconds
If it is not present or the result migration/recording is uncertain, no automatic repeat will be performed; note actions
crashes, the result on the disk should be seen by closing and reopening the application. late
The old answer cannot change this view. Backend wait time is 8 seconds; this time
It is not cancelled. If actual registration has been made, late cancellation will not be considered as undoing the registration.

Generic `save` does not write notes. Old `window.vex.addNote/setNotes` on Native and
`initApp/loadStore` with note cannot bypass permanent authority; returns false. normal
Settings snapshots and interface resets preserve notes. When the initial setting is repaired
The note link is read again. The old native behavior of browser-only mode is preserved.

## Event and tool contract

Native note envelope: `{version:1,request_id,arguments}`. Source and principal are reliable
desktop/local-user is selected by the bridge; It is not retrieved from the UI. All transactions
uses the same registry/policy/single worker line. No new dependencies were added.

| UI event | Core tool | arguments |
|---|---|---|
| notes_init | notes.initialize | `{notes:null}` read only; `{notes:[{text,done}]}` approved first transfer |
| note_add | notes.add | `{text}` |
| note_done | notes.update | `{id,done}`; core can also update text |
| note_del | notes.delete | `{id}` |
| notes_replace | notes.replace | `{notes:[{id,text,done}]}` open backup installation |

The success response contains `{ok:true,completed:true,verified:true,task_id,data}`. CRUD
as a result data.note, initialize/replace as a result data.notes and data.migrated
There is. Failure does not translate into success; In uncertainty comes `unknown:true`. request
The identity is transferred to the manager exactly. Mutations notes.write, listing notes.read
wants. IDs do not change on reopening; The target is not text or string order.

The text is a maximum of 10,000 characters and cannot contain single spaces. done is boolean.
Unknown domain, corrupt record or duplicate id will be rejected. id not found
returns FAILED/not_found; The file is not created/written. Each mutation complete document
verified by reading back; The mismatch is UNKNOWN/commit_unverified. manager
Uncertainty stops new business. Replay block is in open manager session;
persistent task logging and multi-process concurrent writes are not yet available.

## Backup and partial failure

Export protects identities. Old `{t,d}` or text backup gets new ID; new
ID backup preserves existing IDs. Native import validates the file first,
then applies the settings record, followed by the single notes.replace command. local snapshot
does not apply the notes a second time. Note before the first transfer is finished or while the note job is in progress.
import does not start. Controls are preserved throughout import; It opens back up when finished.

The settings file, notes file and localStorage are not single transactions. Settings
successful, not restore may fail; We do not consider this a complete import success.
Backend notes are written and if local cache/skill/routine registration fails,
new grades are not shown as withdrawn; previous local preferences are restored,
partial registration is clearly communicated. The source backup file is not deleted. local cache
error does not ignore the successfully saved backend note.

## Test proof

- `.\.venv\Scripts\python.exe -m pytest -q -W error`: **321 tests passed**.
- Real WebView2: [stage3-native-smoke.json](stage3-native-smoke.json), eight
  process. Real UI add/complete/delete, different IDs with same text, reopen,
  protect form on write rejection, single command on double click, ignore late response,
  import/export, setting recovery and window controls covers.
- [stage3-browser-notes.json](stage3-browser-notes.json): browser-only and
  simulated native. Open old note transfer cancellation/approval, reopen, setter/snapshot
  block, old/new backup, duplicate ID rejection and zero pageerror/rejection.
  The script is work/diagram-check/stage3-browser-notes.mjs in the current workspace.
- Python tests one-time initial transfer on real temporary files,
  The mark remains even if the last note is deleted, corrupt data and write error protection,
  Controls readback obscurity, immutable identity, and permissions.

Native windows are hidden. Confirm selection and export file selection results are in the test.
is controlled; The actual Blob export file is written and its contents are read. These are visible
it is not human dialogical interaction in the window or physical audio/hardware testing.
Tests do not use user data/account. Test report on first native attempts
name clashed with notes.json; reports are separated with the prefix report- and all phases
It was restarted afterwards. Unsuccessful attempts were not counted as implementation success.

## Visible acceptance and next stage

Transfer cancellation/approval, note add/complete/delete, in visible window with isolated TASKVEX_HOME
real Save As/Open with export/import and cancel, real restart and Shutdown
checked. [Visible acceptance certificate](STAGE3_VISIBLE_ACCEPTANCE.md) used
Describes synthetic data and observed results. This visible round of the first transmission is empty
was with the list; Non-empty legacy notes were verified in Python/browser tests.
Planned acceptance of Phase 3 is complete; human UX research or physical voice
It doesn't mean the test has been done. [Stage 4](STAGE4_APPS.md) first application plugin
Describes the steps and the completed catalog slice.


## October 22 — Creation time extension

The note record carries the optional field `created_at`. New addition of backend
UTC writes the ISO millisecond time; normal update/delete arguments field
does not accept. Edit/done protects ID and date. missing/null unknown in old record
It means; Reading old files does not produce a new date or ID. First transfer and
backup restore preserves current space; browser-only time of new note in browser
is taken. Invalid, time-zone-less or non-standard dates are rejected in the calendar.
This field is not a multiple author/sorting warranty. Current limits and tests
[Located in STAGE5_MODEL.md](STAGE5_MODEL.md).
