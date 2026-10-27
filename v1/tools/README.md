# Windows demo build

This directory packages the existing app.main host, not another business-logic
executor. On Windows x64, run from v1 with the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-build.lock.txt
.\.venv\Scripts\python.exe tools/build_demo.py
```

Output: dist/TaskVexDemo-Windows-x64.zip and its SHA256 file. Extract the whole ZIP;
the EXE cannot be moved alone. The separate build lock keeps packaging dependencies
out of the application's runtime declaration. Before creating the ZIP, the script
opens the real frozen WebView2 app with a temporary, keyless profile and fails if
that smoke check fails. License notices are included; BUILD_ENVIRONMENT.json is a
build-environment manifest, not an exact bundled SBOM.

The default demo profile is %LOCALAPPDATA%/TaskVexDemo. Real user settings, credentials
and model caches are not copied. Wake weights are excluded while redistribution
licensing is unresolved; the optional setup command uses the existing verified
upstream downloader. See the package README.txt for prerequisites and usage.

This does not certify clean PCs, real accounts/microphones or frozen restart.
Evidence: logs/reports/demo-build-checks.json at repository root.
