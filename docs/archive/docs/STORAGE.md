# Atomic JSON record — Tier 1, row 6

This document describes the recording layer `v1/app/storage/json_store.py` and `v1/app/config.py`.
Explains data path selection. The purpose is to save old core data to disk.
Do not leave the file unfinished. The UI is not an annotation service or credential repository.

## How does it simply work?

Instead of directly opening the notes.json file and deleting it, the new content is the same.
is written to a unique temporary file in the directory. Write completes, memory buffer
is flushed and fsync is called; After the file is closed, you can restore the original file with os.replace.
is replaced. If an error occurs before replacement, the old record remains in place.

This is atomic replacement: the party reading this file sees the full file, old or new.
Save error returns as an error; Success cannot be made up just because 'it was recorded'.

The file format is as follows; The relevant service verifies the business rules of the fields in the future:

```json
{"version": 1, "data": {"notes": []}}
```

Version specifies the file format; It is not a record revision. Conversion from old version
There is not yet. The unsupported version cannot be read or written to; so a new
The app's data will not be accidentally deleted by the old version.

## Data location and usage

Whenever get_data_home() is called it first looks at TASKVEX_HOME. Absolute if set
There must be a way. Otherwise, %LOCALAPPDATA%/TaskVex is selected on Windows. relative/null
setting is error; Writing to the source directory does not fall back. Import and create objects
file/directory does not create; The directory was created during the first write.

```python
from app.config import get_data_home
from app.storage.json_store import JsonStore

# These calls use the actual data directory; In tests TASKVEX_HOME is temporary.
store = JsonStore(get_data_home() / "notes.json")
current = store.read()  # None if the file does not exist; {} if valid empty object.
# store.write({"notes": []}) is only called when the service explicitly wants to save.
```

read returns a new object. Changing the read dictionary does not change the disk.
write accepts only JSON objects: null/False/0 is protected; tuple, private object,
Non-text keys, loops, and infinite numbers are rejected. This border is common
It uses the contracts.copy_json helper. Duplicate JSON keys on disk also
It is not accepted by silently selecting the last value.

## Corrupt file and error behavior

| Status | Behavior |
|---|---|
| File does not exist yet | read → None; no automatic file creation |
| Valid empty data | read → {}; separate from missing file |
| Corrupt JSON/UTF-8/zarf | corrupt_data; original file preserved, overwrite denied |
| Unsupported version | unsupported_version; delete/reset not done |
| Read/write access error | read_failed/write_failed; content not carried over to error message |
| Invalid new data in memory | invalid_data; disk untouched |

To recover the corrupted file, the host must explicitly make the error condition visible
It can call recover_corrupt(). This method only fixes the corrupted file with the unique `.corrupt`
moves on behalf of and returns the backup path; The actual bytes do not change. After this read
ReturnsNone. The decision to import Default/data rests with the service. healthy file
real estate; It is not reset under the pretext of version or access error recovery.
If the recovery migration fails, recovery_failed returns and remains in place.
The optional validate callback also checks the application schema: ContractError
The rejected record can be preserved and moved; unexpected validator error healthy
It does not move data because it is corrupt. The old usage without argument is retained. Native settings repair
uses this method with explicit user consent; detail in STAGE2_NATIVE.md.

## Borders

- Single host/printer is assumed; The read → modify → write sequence is a transaction
  It is not. If parallel services or a second application process will be written in the future
  lock/transaction is also required to prevent lost update.
- The path is chosen by the trusted host. This class contains the file path from the model
  It is not an authorizing file agent or symlink security boundary.
- API key/token/password this is not put into ordinary JSON files. encryption or
  credential management was not added; The calling service must select the data fields that are allowed.
- If the process suddenly shuts down, `.tmp` may remain orphaned; registration is not counted at startup and
  It is not imported automatically. In normal error paths, the temporary file is cleared; cleaning
  If his/her access is also disabled, he/she can now stay. There is no automatic residual file cleaner.
- fsync + replace is used in the same directory; hardware failure, power outage,
  network/shared file system and OneDrive sync are not warrantied.
  The production default is LOCALAPPDATA, not the source code under OneDrive.
- UI localStorage not moved/changed. Note tools and native connection
  will use this recording layer in the next stages.

## Denenenler

`v1` in `.\.venv\Scripts\python.exe -m pytest -q -W error`:
**184 tests passed**; 44 records/path tests added to the previous 140 tests. real temporary
read/write, UTF-8, empty/incomplete separation with files, corrupted data recovery, version rejection
Partial write to temporary file, fsync/replace/directory/access errors confirmed.
The child Python process was abruptly terminated with os._exit before replace; previous
It was observed that the record could be read and the temporary file was no longer used.

Real power outage, multi-process co-authoring and native UI have not been tried.
The actual recording line with the notes.add/list has now also been tested; current **215 tests**
and Stage 1 acceptance results are in [STAGE1_CORE.md](STAGE1_CORE.md).
