"""Find an authenticated local service and reserve its port before publishing credentials."""
import errno
import json
import os
from pathlib import Path
import socket
import sys


def registry_file():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'KujiDesk' / 'active-runtime.json'


def remember_runtime(runtime):
    path=registry_file()
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps({'runtime':str(Path(runtime).resolve())}),encoding='utf-8')
    temp.replace(path)


def resolve_runtime(preferred, probe):
    preferred=Path(preferred)
    if probe(preferred):return preferred
    try:
        candidate=Path(json.loads(registry_file().read_text(encoding='utf-8'))['runtime'])
        if candidate!=preferred and probe(candidate):return candidate
    except (OSError,ValueError,KeyError,TypeError):
        pass
    return preferred


def bind_listener(port=18766):
    listener=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        if os.name=='nt':listener.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        listener.bind(('127.0.0.1',port))
        listener.listen(128)
        listener.setblocking(False)
        return listener
    except OSError as error:
        listener.close()
        if error.errno==errno.EADDRINUSE or getattr(error,'winerror',None)==10048:return None
        raise


def background_environment():
    if not getattr(sys, 'frozen', False):
        return None
    # The service and notifier can outlive the one-file process that started them.
    env = {**os.environ, 'PYINSTALLER_RESET_ENVIRONMENT': '1'}
    bundled = Path(sys._MEIPASS).resolve()
    node = env.get('PLAYWRIGHT_NODEJS_PATH')
    if node and Path(node).resolve().is_relative_to(bundled):
        env.pop('PLAYWRIGHT_NODEJS_PATH')
    return env
