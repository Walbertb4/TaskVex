# Stage 1 / sequence 1 — Python environment

October 21, 2026. Completed scope: v1/.venv, pyproject.toml, development testing tool and temporary data isolation. Core contracts/executor has not been written yet.

- The environment was created with Python 3.14.7 available on the system; The project minimum was specified as Python 3.11. No testing on other Python versions yet.
- There is no production dependency for now. No pywebview, Gemini, audio or Mark dependencies installed.
- pyproject.toml is the only dependency declaration source. dev group contains pytest>=9,<10; The solved version is pytest 9.1.1.
- requirements-dev.lock.txt is the full version snapshot of installed development packages; It is not a second list to be manually managed independent of pyproject.toml. A universal lock or broadcast containing a hash is not considered a security guarantee.
- tests/conftest.py defines temporary TASKVEX_HOME per test. The environment variable should be read in the bootstrap phase while writing the application config module; Testing should not be done with real user data.
- pip check passed. pyproject TOML parsed; correct project and empty runtime dependencies verified; Verified interpreter is working in venv.
- pytest collection command worked; Since there is no behavioral testing yet, `no tests collected` / exit 5 is the expected result. This does not mean that the core tests have passed. Real core tests will be added in Phase 1 / sequence 2 and beyond.

Installation/running commands: [v1 README](../v1/README.md).

## Note correction

Three local save calls in notes.js were emitSave:false. Insertion, completion and deletion only send the relevant note_* mutation. Management of records with the same text by identity, UI based on backend approval and rollback in case of record error are not the scope of this small change; It will be discussed in the native grade transition. HTML/CSS appearance has not been changed.

Browser proof: [note-events-fix.json](note-events-fix.json). Native migration is simulated; actual PyWebView untested.
