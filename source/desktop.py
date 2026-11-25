"""Windowed executable entry point, also used for its notification helper."""
import json
import multiprocessing
import os
from pathlib import Path
import sys


def run():
    multiprocessing.freeze_support()
    folder=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
    pointer=folder/'KujiDesk.runtime.json'
    if pointer.exists() and not os.environ.get('KUJI_RUNTIME'):
        data=json.loads(pointer.read_text(encoding='utf-8'))
        os.environ['KUJI_RUNTIME']=str(Path(data['runtime']).resolve())
    import manager
    if '--self-test' in sys.argv:
        import playwright
        output=Path(sys.argv[sys.argv.index('--self-test')+1])
        driver=Path(os.environ.get('PLAYWRIGHT_NODEJS_PATH', Path(playwright.__file__).parent/'driver'/'node.exe'))
        import asyncio
        async def check_driver():
            from playwright.async_api import async_playwright
            async with async_playwright() as driver:
                return driver.chromium.name == 'chromium'
        driver_working = asyncio.run(check_driver())
        result={'ok':driver_working and (manager.HERE/'web'/'index.html').exists() and driver.exists(),
                'web_assets':(manager.HERE/'web'/'index.html').exists(),
                'playwright_driver':driver.exists(),'driver_working':driver_working,'frozen':bool(getattr(sys,'frozen',False)),
                'runtime':str(manager.DEFAULT_RUNTIME)}
        import tkinter
        result['tk_version']=str(tkinter.Tcl().call('info','patchlevel'))
        from native_ui import NativeUI
        root=tkinter.Tk();root.withdraw()
        ui=NativeUI(manager.DEFAULT_RUNTIME,root=root,connect=False)
        root.update_idletasks()
        result['native_ui']=True
        ui.discord_settings()
        root.update_idletasks()
        result['discord_settings']=bool(ui.discord_dialog.winfo_exists())
        ui.discord_dialog.destroy()
        ui.close()
        output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        return
    runtime=manager.DEFAULT_RUNTIME
    if '--runtime' in sys.argv:
        runtime=Path(sys.argv[sys.argv.index('--runtime')+1])
    if '--server' not in sys.argv and '--notifier' not in sys.argv and '--runtime' not in sys.argv:
        from native_ui import Client
        from service_runtime import resolve_runtime
        runtime=resolve_runtime(runtime,lambda folder:Client(folder).alive())
    runtime.mkdir(parents=True,exist_ok=True)
    if getattr(sys,'frozen',False):
        log=(runtime/'desktop.log').open('a',encoding='utf-8',buffering=1)
        sys.stdout=sys.stderr=log
    if '--notifier' in sys.argv:
        sys.argv.remove('--notifier')
        import notifications
        notifications.main()
    elif '--server' in sys.argv:
        sys.argv.remove('--server')
        manager.main()
    else:
        from native_ui import NativeUI
        NativeUI(runtime).run()


if __name__=='__main__':
    try:
        run()
    except Exception:
        import traceback
        traceback.print_exc()
        if os.name=='nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,'無法啟動 Kuji Desk。請查看本機 Runtime 的 desktop.log。','Kuji Desk',16)
