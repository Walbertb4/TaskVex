# Stage 3 — Visible Windows acceptance

This document is visible from previous hidden WebView2 and simulated dialog tests
window/real saves the file dialog control. Date: October 21, 2026.
The Windows interface was used with Computer Use (`@oai/sky`); approval and file
their dialogue was not altered or imitated. This human usability
It is not a research or physical sound test.

## Insulation

The application is opened with separate TASKVEX_HOME:
`C:/Users/batue/Documents/Codex/2026-10-20/mi/work/stage3-visible-acceptance`.
The user's actual TaskVex data directory was not used. Text of single note created
It was `Stage 3 visible acceptance`; All add/delete/restore transactions are synthetic
Made on note. The first transfer check used the empty local list;
Transfer of non-empty old records has been verified by previous Python/browser tests.

## Observed results

| Control | Conclusion |
|---|---|
| Visible start | Observed purple theme, reactor, panels and MODEL OFFLINE status; note standby message and transfer button can be read |
| Cancel first transfer | Cancel was selected in the actual confirm window; notes.json was not created, notes checks remained pending |
| Confirm initial transfer | OK was selected in the actual confirm window; grade checks turned on and one-time transfer mark written |
| Add notes | The actual input field and + button were used; notes view and notes.json matched |
| Note completion | Checkbox clicked; crossed out in view, verified done=true on disk |
| Real export | Windows Save As was opened with Settings > System > Export; the file is saved in the test directory; JSON content read |
| Export cancellation | In the second actual Save As dialog, Cancel was selected; The application did not report that the file was written |
| Delete note | Only the ✕ button of the synthetic note was used; verified notes=[] and ui_migrated=true on disk |
| Real import | JSON was just selected from the Windows Open dialog; note came back with the same id and done=true; success status shown |
| Import cancellation | The second real Open dialogue was aborted with Escape; grades unchanged |
| Real restart | UI Restart app button used; old window closed and new process opened with different window ID |
| reopening | The completed appearance of the note, its identity, and its remaining as a single record have been verified; no retransmission requested |
| Normal closing | UI Shutdown was used; It was also checked that the test window was closed |

id/t/d fields of the note in the backup `visible-backup.json` file, in the backend file
the same id/text/done areas were compared. Identity equality and done=true one
Also checked with assertion. Screenshots during checkup
seen; No image file archives have been added to this document.

## Tool limits and scope

Some UI Automation elements display invalid coordinates when opening the modal/download panel.
gave. New observation received; current screen coordinate or normal display where necessary
keyboard was used. When you turn off the WebView2 download notification setting button, you go to the settings.
Accessed with the current Ctrl+K > Settings command. These errors are called successful clicks.
not counted. The actual file write and backend result was also verified from the file.

Previous of Phase 3 **321 Python**, **8 hidden native processes** and **2 browsers**
Its acceptance is completed by this visible control. After Stage 4 catalog addition, all
The Python suite also passed **332**. No new UI fixes were required in this apparent round.
True account/hardware, multi-process write and shared transaction to separate repositories
No guarantee is given. Next development is in [Phase 4](STAGE4_APPS.md).
