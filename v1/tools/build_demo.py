"""Compile Windows x64 demo package with clean data; Never copy personal profile.

Only app resources, UI assets and installed dependencies are imported. PyInstaller
The output of onedir is put into ZIP; EXE does not migrate by itself. Build dependency is in separate lock.
"""
from hashlib import sha256
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def build():
    if sys.platform != 'win32' or sys.maxsize <= 2**32:
        raise SystemExit('Build requires Windows x64 Python')
    output, work = ROOT/'dist', ROOT/'build'/'demo'
    command = [sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed',
        '--name','TaskVexDemo','--distpath',str(output),'--workpath',str(work),'--specpath',str(work),
        '--paths',str(ROOT),'--add-data',f'{ROOT / "ui" / "index.html"};ui',
        '--add-data',f'{ROOT / "ui" / "styles.css"};ui',
        '--add-data',f'{ROOT / "ui" / "js"};ui/js',
        '--add-data',f'{ROOT / "ui" / "assets"};ui/assets',
        '--collect-all','sherpa_onnx','--collect-all','clr_loader','--collect-all','pythonnet',
        '--collect-submodules','winrt','--copy-metadata','google-genai',
        '--exclude-module','pytest','--exclude-module','tkinter','--exclude-module','PyQt5',
        '--exclude-module','PyQt6','--exclude-module','PySide2','--exclude-module','PySide6',
        str(ROOT/'tools'/'demo_entry.py')]
    subprocess.run(command,cwd=ROOT,check=True)
    package = output/'TaskVexDemo'
    shutil.copy2(ROOT.parent/'LICENSE',package/'LICENSE.txt')
    shutil.copy2(ROOT/'tools'/'DEMO_README.txt',package/'README.txt')
    (package/'Setup wake model.cmd').write_text('@echo off\r\necho Downloading the optional wake model. Please wait...\r\n"%~dp0TaskVexDemo.exe" --setup-wake\r\n',encoding='ascii')
    # license/metadata only; There is no environment variable, pip URL credential or user data.
    notices = package/'THIRD_PARTY_NOTICES'
    installed = []
    for distribution in metadata.distributions():
        name = distribution.metadata['Name']
        installed.append({'name':name,'version':distribution.version})
        for file in distribution.files or []:
            source = Path(str(distribution.locate_file(file)))
            if any(label in file.name.upper() for label in ('LICENSE','NOTICE','COPYING')) and source.is_file():
                target = notices/name/str(file)
                if not target.resolve().is_relative_to(notices.resolve()):
                    raise ValueError('License target outside notices directory')
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,target)
    (package/'BUILD_ENVIRONMENT.json').write_text(json.dumps(installed,indent=2),encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='taskvex-exe-') as temp:
        home = Path(temp)
        environment = dict(os.environ,TASKVEX_HOME=str(home/'profile'))
        for key in ('GEMINI_API_KEY','GOOGLE_API_KEY','GOOGLE_APPLICATION_CREDENTIALS'):
            environment.pop(key,None)
        report = home/'smoke.json'
        subprocess.run([str(package/'TaskVexDemo.exe'),'--smoke-report',str(report)],cwd=home,
            env=environment,timeout=90,check=True)
        result = json.loads(report.read_text(encoding='utf-8'))
        if not result['ok']:raise RuntimeError('Packaged smoke failed')
        evidence = ROOT.parent/'logs'/'reports'/'demo-build-smoke.json'
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(json.dumps(result,indent=2),encoding='utf-8')
    archive = Path(shutil.make_archive(str(output/'TaskVexDemo-Windows-x64'),'zip',output,'TaskVexDemo'))
    digest = sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n',encoding='ascii')
    print(json.dumps({'exe':str(package/'TaskVexDemo.exe'),'zip':str(archive),'bytes':archive.stat().st_size,'sha256':digest}))


if __name__ == '__main__':
    build()
