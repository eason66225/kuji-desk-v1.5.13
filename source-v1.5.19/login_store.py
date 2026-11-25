"""Local Windows-user encrypted cookie snapshots. Never logs cookie contents."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import time


class Blob(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def protect(data, decrypt=False):
    if os.name != 'nt':
        raise OSError('Login snapshots require Windows account encryption')
    buf = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)))
    dest = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    fn = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                   ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    fn.restype = wintypes.BOOL
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(dest)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(dest.data, dest.size)
    finally:
        kernel.LocalFree(ctypes.cast(dest.data, ctypes.c_void_p))


def site_cookies(cookies):
    return [c for c in cookies if
            (c.get('domain', '').lstrip('.') == 'on-line.1kuji.com'
             or c.get('domain', '').lstrip('.') == '1kuji.com')
            and (c.get('expires', -1) == -1 or c.get('expires', 0) > time.time())]


def save(path, cookies):
    cookies = site_cookies(cookies)
    if not cookies:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sealed = protect(json.dumps(cookies).encode('utf-8'))
    temp = path.with_suffix('.tmp')
    with temp.open('wb') as stream:
        stream.write(sealed)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def restore(path, current):
    path = Path(path)
    if not path.exists():
        return []
    saved = site_cookies(json.loads(protect(path.read_bytes(), decrypt=True)))
    existing = {(c['name'], c['domain'], c['path']) for c in site_cookies(current)}
    # Existing browser cookies win; do not roll back a newer login.
    return [c for c in saved if (c['name'], c['domain'], c['path']) not in existing]
