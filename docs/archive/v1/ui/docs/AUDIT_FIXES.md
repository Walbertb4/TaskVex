# Corrections after independent audit

Fixed findings R01–R14 at contract level UI/browser:

- Snapshot additional fields and old local records are validated; corrupted areas are recovered without deleting valid data.
- Skill/routine IDs are collision checked on all input paths; Explicit repeat IDs are rejected.
- Backend location notification does not produce outbound saves; Observer native does not lock the result.
- Ready notification is sent after the camera state is established.
- Old talk and shutdown timers cannot affect the new state/Restart.
- Failed form registrations are rolled back; Retrying does not create a double registration.
- Bearer error format is masked; Broken timeline does not crash the search.
- Clears open empty catalog options; Zero time resets the counter correctly.
- Modals use focus and dialog semantics; background interaction is limited.

See [Current contract](UI_BACKEND_CONTRACT.md). HTML/CSS and the design has not changed. Verifications were performed in the local HTTP/Edge environment with synthetic backend; The actual native/hardware/external is not a service confirmation.
