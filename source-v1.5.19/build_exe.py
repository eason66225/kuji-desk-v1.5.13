"""Build a single Windows EXE, excluding every Runtime file and account profile."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import manager
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
SHARE = '--share' in sys.argv
DIST=HERE.parent/('KujiDesk-share-v1.5.19' if SHARE else 'KujiDesk-v1.5.19')
WORK=manager.DEFAULT_RUNTIME/'pyinstaller'
DIST.mkdir(parents=True,exist_ok=True)
WORK.mkdir(parents=True,exist_ok=True)
with sync_playwright() as playwright:
    firefox = manager.firefox_executable(playwright.firefox)
if not firefox.is_file():
    raise SystemExit('Run python -m playwright install firefox before building Kuji Desk.')
command=[sys.executable,'-m','PyInstaller','--noconfirm','--onefile','--windowed',
         '--name','KujiDesk','--icon',str(HERE/'logo.ico'),'--add-data',str(HERE/'logo.png')+os.pathsep+'.','--distpath',str(DIST),'--workpath',str(WORK),
         '--specpath',str(HERE),'--add-data',str(HERE/'web')+os.pathsep+'web',
         '--collect-all','playwright', '--copy-metadata','playwright',str(HERE/'desktop.py')]
subprocess.run(command,check=True,cwd=HERE)
shutil.copytree(firefox.parent, DIST/'firefox', dirs_exist_ok=True)
# Machine-specific pointer is deliberately separate from the executable.
if not SHARE:
    (DIST/'KujiDesk.runtime.json').write_text(json.dumps({'runtime':str(manager.DEFAULT_RUNTIME.resolve())},ensure_ascii=False,indent=2),encoding='utf-8')
print(str(DIST/'KujiDesk.exe'))
