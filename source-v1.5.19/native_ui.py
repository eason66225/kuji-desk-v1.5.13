"""Native Windows/Tk UI. Queue automation stays in the authenticated local service."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import queue
import subprocess
from service_runtime import background_environment
import sys
from threading import Lock
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from urllib.error import HTTPError
from urllib.request import Request, urlopen

VERSION='1.5.19'
UI_VERSION='1.5.19'
BG='#10151c'; PANEL='#18212c'; TEXT='#eef3f8'; MUTED='#a0aec0'; LIME='#d7f896'
RED='#e05252'; GREEN='#38a169'
COLORS={'A':'#8bb9ff','B':'#d7f896','C':'#ffbe84'}


class Client:
    def __init__(self,runtime):
        self.runtime=Path(runtime)
        self.server_lock=Lock()

    def call(self,path='state',data=None,timeout=40):
        auth=json.loads((self.runtime/'panel-session.json').read_text(encoding='utf-8'))
        headers={'Authorization':'Bearer '+auth['token']}
        body=None
        if data is not None:
            headers['Content-Type']='application/json';body=json.dumps(data).encode()
        try:
            with urlopen(Request('http://127.0.0.1:18766/api/'+path,data=body,headers=headers),timeout=timeout) as response:
                return json.load(response)
        except HTTPError as error:
            try: message=json.loads(error.read()).get('error','操作失敗')
            except (ValueError,AttributeError):message='目前服務版本不支援此操作，請按「重新啟動服務」套用新版。'
            raise ValueError(message) from None
        except TimeoutError:
            action=(data or {}).get('action',path)
            raise ValueError(f'本機總控等候逾時（{action}）；操作結果尚未確認，請看執行紀錄，勿重複提交。') from None

    def alive(self):
        try:return self.call(timeout=2)
        except Exception:return None

    def spawn_server(self, login_only=False):
        command=([sys.executable,'--server'] if getattr(sys,'frozen',False)
                 else [sys.executable,str(Path(__file__).with_name('manager.py'))])
        log=(self.runtime/'native-server.log').open('a',encoding='utf-8')
        command += ['--runtime', str(self.runtime), '--no-browser']
        if login_only:
            command.append('--login-only')
        subprocess.Popen(command,stdin=subprocess.DEVNULL, env=background_environment(),
            stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)

    def ensure_server(self, login_only=False):
        with self.server_lock:
            current = self.alive()
            if not current:
                self.spawn_server(login_only=login_only)
                for _ in range(40):
                    current = self.alive()
                    if current:
                        break
                    time.sleep(.25)
                else:
                    raise ValueError('本機服務未成功啟動，請查看 Runtime 的 native-server.log。')
            if current.get('loginOnly') and not login_only:
                self.call('control', {'action':'resume'})

    def restart_server(self):
        current=self.alive()
        login_only = bool(current and current.get('loginOnly'))
        if current:
            if 'loginOnly' in current or current.get('version')==VERSION:
                self.call('control',{'action':'shutdown','confirmed':True})
            else:
                self.stop_legacy_server()
            for _ in range(120):
                if not self.alive():break
                time.sleep(.25)
            else:raise ValueError('舊服務尚未停止，沒有啟動另一份服務。')
        self.ensure_server(login_only=login_only)

    def stop_legacy_server(self):
        # Only the authenticated service's recorded PID owning our local port.
        pid=int((self.runtime/'manager.pid').read_text(encoding='utf-8-sig').strip())
        script=(f'$p=Get-CimInstance Win32_Process -Filter "ProcessId = {pid}"; '
                '$o=@(Get-NetTCPConnection -LocalPort 18766 -State Listen -ErrorAction SilentlyContinue); '
                '[pscustomobject]@{Pid=$p.ProcessId;Name=$p.Name;Command=$p.CommandLine;Owners=@($o.OwningProcess)} | ConvertTo-Json -Compress')
        flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command',script],creationflags=flags)
        process=json.loads(raw.decode('utf-8-sig',errors='replace'))
        command=str(process.get('Command','')).lower().replace('\\','/')
        own_command=('kuji-manager/manager.py' in command or 'kujidesk.exe' in command)
        if process.get('Pid')!=pid or pid not in process.get('Owners',[]) or not own_command:
            raise ValueError('無法核對舊總控的程序身分，未強制終止。')
        subprocess.run(['taskkill.exe','/PID',str(pid),'/T','/F'],check=True,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)


def stamp(value):
    return time.strftime('%H:%M:%S',time.localtime(value/1000)) if value else '—'


class NativeUI:
    def __init__(self,runtime,root=None,connect=True):
        self.runtime=Path(runtime);self.client=Client(runtime)
        self.root=root or tk.Tk();self.root.title('suto 1 ban kuji · 獨立視窗 v'+UI_VERSION)
        self.root.geometry('1280x980');self.root.minsize(1080,850);self.root.configure(bg=BG)
        self.icon=tk.PhotoImage(file=str(Path(__file__).with_name('logo.png')))
        self.root.iconphoto(True,self.icon)
        self.pool=ThreadPoolExecutor(max_workers=5);self.results=queue.Queue()
        self.service_version=None
        self.accounts={};self.cards={};self.busy=set();self.polling=False;self.closed=False
        self.connection=tk.StringVar(value='正在連接本機服務…')
        self.notice=tk.StringVar(value='關閉此視窗不會自動退出網站隊伍。')
        self.url=tk.StringVar(value='https://on-line.1kuji.com/Form/Product/SelectBox.aspx?pid=sap_0000008694&pno=1')
        self.count=tk.StringVar(value='70');self.low=tk.StringVar(value='2.2');self.high=tk.StringVar(value='4.5')
        self.auto=tk.BooleanVar(value=True)
        self.entry_refresh=tk.BooleanVar(value=True)
        self.auto_refresh_inv=tk.BooleanVar(value=True)
        self.last_auto_inv_time=time.time()
        self.load_settings()
        self.setup_styles();self.build()
        self.render({'loginOnly':True, 'accounts':[]})
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.root.after(100,self.drain)
        if connect:
            self.root.after(600,self.poll)

    def setup_styles(self):
        style=ttk.Style(self.root);style.theme_use('clam')
        style.configure('Treeview',background='#121923',fieldbackground='#121923',foreground=TEXT,
                        borderwidth=0,bordercolor='#2a3543',lightcolor='#121923',darkcolor='#121923',
                        rowheight=26,font=('Microsoft JhengHei UI',10))
        style.configure('Treeview.Heading',background='#202c3a',foreground=MUTED,relief='flat',borderwidth=0,
                        bordercolor='#202c3a',lightcolor='#202c3a',darkcolor='#202c3a',font=('Microsoft JhengHei UI',10))
        style.layout('Treeview',[('Treeview.treearea',{'sticky':'nswe'})])
        style.configure('Vertical.TScrollbar',background='#314253',troughcolor='#121923',borderwidth=0,
                        bordercolor=PANEL,lightcolor='#314253',darkcolor='#314253',arrowcolor=MUTED,width=11)
        # Clam inherits light active/pressed heading colors unless each state
        # is mapped explicitly. Do not let hover fall back to system white.
        heading_states=['disabled','pressed','active','focus']
        style.map('Treeview.Heading',
                  background=[(state,'#202c3a') for state in heading_states],
                  foreground=[(state,MUTED) for state in heading_states],
                  bordercolor=[(state,'#202c3a') for state in heading_states],
                  lightcolor=[(state,'#202c3a') for state in heading_states],
                  darkcolor=[(state,'#202c3a') for state in heading_states],
                  relief=[(state,'flat') for state in heading_states])
        style.map('Treeview',background=[('selected','#334c60')],
                  foreground=[('selected',TEXT)])
        style.map('Vertical.TScrollbar',
                  background=[('disabled','#263442'),('pressed','#3b5064'),('active','#3b5064')],
                  arrowcolor=[('disabled','#69788a'),('active',MUTED),('pressed',MUTED)],
                  bordercolor=[('active',PANEL),('pressed',PANEL)],
                  lightcolor=[('active','#3b5064'),('pressed','#3b5064')],
                  darkcolor=[('active','#3b5064'),('pressed','#3b5064')])

    def label(self,parent,text=None,var=None,size=11,color=TEXT,bold=False,**kwargs):
        kwargs.setdefault('anchor','w')
        return tk.Label(parent,text=text,textvariable=var,bg=parent.cget('bg'),fg=color,
                        font=('Microsoft JhengHei UI',size,'bold' if bold else 'normal'),**kwargs)

    def button(self,parent,text,command,primary=False,bg=None,fg=None):
        btn_bg = bg or (LIME if primary else '#283648')
        btn_fg = fg or ('#16220d' if primary else TEXT)
        return tk.Button(parent,text=text,command=command,bg=btn_bg,
                         fg=btn_fg,activebackground=btn_bg,
                         activeforeground=btn_fg,highlightthickness=0,
                         disabledforeground='#6b7786',relief='flat',padx=10,pady=7,
                         font=('Microsoft JhengHei UI',10,'bold' if bg or primary else 'normal'),cursor='hand2')

    def build(self):
        # Top Menu bar
        menubar = tk.Menu(self.root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label='🔔 Discord Webhook 通知設定...', command=self.discord_settings)
        settings_menu.add_command(label='💾 儲存監看秒數與籤數設定', command=self.save_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label='❌ 離開', command=self.close)
        menubar.add_cascade(label='設定 (S)', menu=settings_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label='執行紀錄', command=self.show_logs)
        tools_menu.add_command(label='🔄 重新整理介面 (F5)', command=self.reload_gui)
        tools_menu.add_command(label='⚡ 開啟／關閉控制台', command=self.toggle_control)
        tools_menu.add_command(label='🔁 重新啟動背景服務', command=self.restart_service)
        menubar.add_cascade(label='工具 (T)', menu=tools_menu)
        self.root.config(menu=menubar)
        self.root.bind('<F5>', lambda e: self.reload_gui())

        header=tk.Frame(self.root,bg=BG);header.pack(fill='x',padx=24,pady=(18,12))
        self.label(header,'suto 1 ban kuji',size=22,color=LIME,bold=True).pack(side='left')
        self.label(header,'三個帳號 · 獨立 Windows 視窗',color=MUTED).pack(side='left',padx=20)
        self.button(header,'執行紀錄',self.show_logs).pack(side='right',padx=4)
        self.button(header,'重新啟動服務',self.restart_service).pack(side='right')
        self.btn_control = self.button(header,'開啟控制台',self.toggle_control,bg=GREEN,fg='#ffffff')
        self.btn_control.pack(side='right',padx=8)
        self.button(header,'🔔 DC Webhook 設定',self.discord_settings,bg='#2b3d52',fg='#ffffff').pack(side='right')
        self.label(self.root,var=self.connection,color=MUTED,anchor='w').pack(fill='x',padx=24)
        settings=tk.Frame(self.root,bg=PANEL,padx=16,pady=12);settings.pack(fill='x',padx=24,pady=12)
        self.label(settings,'商品／選箱網址（可先填網站首頁）',size=10,color=MUTED).grid(row=0,column=0,sticky='w')
        tk.Entry(settings,textvariable=self.url,bg='#101720',fg=TEXT,insertbackground=TEXT,
                 relief='flat',font=('Segoe UI',10)).grid(row=1,column=0,sticky='ew',ipady=7,padx=(0,12))
        for col,(label,var) in enumerate([('目標籤數',self.count),('最短秒數',self.low),('最長秒數',self.high)],1):
            self.label(settings,label,size=10,color=MUTED).grid(row=0,column=col,sticky='w')
            tk.Entry(settings,textvariable=var,width=8,bg='#101720',fg=TEXT,insertbackground=TEXT,
                     relief='flat').grid(row=1,column=col,padx=5,ipady=7)
        settings.columnconfigure(0,weight=1)
        tk.Checkbutton(settings,text='箱子售完後自動找新箱',variable=self.auto,bg=PANEL,fg=TEXT,
                       selectcolor=BG,activebackground=PANEL,activeforeground=TEXT).grid(row=2,column=0,sticky='w',pady=(8,0))
        self.button(settings,'停止全部監看',lambda:self.batch('stop'),bg=RED,fg='#ffffff').grid(row=2,column=1,columnspan=2,pady=(8,0))
        self.button(settings,'一起開始監看',lambda:self.batch('start'),bg=GREEN,fg='#ffffff').grid(row=2,column=3,pady=(8,0))
        tk.Checkbutton(settings,text='啟用入場重新整理功能',variable=self.entry_refresh,bg=PANEL,fg=TEXT,
                       selectcolor=BG,activebackground=PANEL,activeforeground=TEXT).grid(row=3,column=0,sticky='w',pady=(4,0))
        tk.Checkbutton(settings,text='每 3 分鐘自動以 API 更新全部籤數',variable=self.auto_refresh_inv,bg=PANEL,fg=TEXT,
                       selectcolor=BG,activebackground=PANEL,activeforeground=TEXT).grid(row=4,column=0,sticky='w',pady=(4,0))
        self.button(settings,'更新全部籤數',lambda:self.batch('api_inventory')).grid(
            row=4,column=1,columnspan=2,padx=8,pady=(4,0))
        self.button(settings,'儲存秒數／監看設定',self.save_settings).grid(row=4,column=3,sticky='e',pady=(4,0))
        cards=tk.Frame(self.root,bg=BG);cards.pack(fill='both',expand=True,padx=24,pady=(0,12))
        for col,ident in enumerate('ABC'):
            cards.columnconfigure(col,weight=1,uniform='card');cards.rowconfigure(0,weight=1)
            f=tk.Frame(cards,bg=PANEL,padx=14,pady=12,highlightbackground='#2b3848',highlightthickness=1)
            f.grid(row=0,column=col,sticky='nsew',padx=(0,10 if col<2 else 0))
            title=self.label(f,f'{ident}   帳號 {ident}',size=16,color=COLORS[ident],bold=True);title.pack(anchor='w')
            phase=self.label(f,'未連接',color=MUTED);phase.pack(anchor='w',pady=(4,0))
            rank=self.label(f,'—',size=25,color=COLORS[ident],bold=True);rank.pack(anchor='w',pady=(12,0))
            box=self.label(f,'目前箱子：—',size=10,color=MUTED);box.pack(anchor='w')
            note=self.label(f,'',size=10,color=TEXT,anchor='nw',justify='left',wraplength=340,height=3);note.pack(fill='x',pady=(10,8))
            stock=self.label(f,'剩餘籤數：—',size=36,color=LIME,bold=True);stock.pack(anchor='w',pady=(4,2))
            tree=ttk.Treeview(f,columns=('prize','left'),show='headings',height=10)
            tree.heading('prize',text='賞別');tree.heading('left',text='剩餘／原始')
            tree.column('prize',width=95,stretch=True);tree.column('left',width=115,stretch=True,anchor='center')
            tree.tag_configure('even',background='#16202b')
            tree.tag_configure('odd',background='#121923')
            tree.tag_configure('zero',foreground='#c59772',background='#121923')
            tree.pack(fill='both',expand=True,pady=(8,4))
            updated=self.label(f,'尚未讀取箱子資訊',size=9,color=MUTED);updated.pack(anchor='w')
            actions=tk.Frame(f,bg=PANEL);actions.pack(fill='x',pady=(10,0))
            actions.columnconfigure(0,weight=1);actions.columnconfigure(1,weight=1)
            buttons={}
            for row,pair in enumerate([ [('open','開啟／登入'),('monitor','開始監看')],
                                        [('requeue','離開目前箱並監看'),('inspect','重新查看／修復')],
                                        [('restart','重啟此帳號視窗'),('rename','修改帳號名稱')],
                                        ]):
                for column,(action,text) in enumerate(pair):
                    b=self.button(actions,text,lambda i=ident,a=action:self.act(i,a),action=='monitor')
                    b.grid(row=row,column=column,sticky='ew',padx=2,pady=3);buttons[action]=b
            # Keep controls visible when the window is shorter; only the stock
            # table flexes and scrolls instead of pushing recovery buttons away.
            f.columnconfigure(0,weight=1);f.rowconfigure(6,weight=1)
            widgets=[title,phase,rank,box,note,stock,tree,updated,actions]
            for widget in widgets:
                widget.pack_forget()
            for row,widget in enumerate(widgets):
                widget.grid(row=row,column=0,sticky='nsew' if row==6 else 'ew',pady=3)
            scrollbar=ttk.Scrollbar(f,orient='vertical',command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.grid(row=6,column=1,sticky='ns')
            self.cards[ident]={'frame':f,'title':title,'phase':phase,'rank':rank,'box':box,'note':note,
                               'stock':stock,'tree':tree,'updated':updated,'buttons':buttons,'stock_key':None}
        self.label(self.root,var=self.notice,size=10,color=MUTED,anchor='w',justify='left').pack(fill='x',padx=24,pady=(0,14))

    def load_settings(self):
        settings_file = self.runtime / 'ui-settings.json'
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text(encoding='utf-8'))
                if 'url' in data: self.url.set(str(data['url']))
                if 'count' in data: self.count.set(str(data['count']))
                if 'minSeconds' in data: self.low.set(str(data['minSeconds']))
                if 'maxSeconds' in data: self.high.set(str(data['maxSeconds']))
                if 'autoResumeSoldOut' in data: self.auto.set(bool(data['autoResumeSoldOut']))
                if 'entryRefresh' in data: self.entry_refresh.set(bool(data['entryRefresh']))
                if 'autoRefreshInventory' in data: self.auto_refresh_inv.set(bool(data['autoRefreshInventory']))
            except Exception:
                pass

    def save_settings(self, silent=False):
        try:
            cfg = self.config()
            if cfg['minSeconds'] <= 0 or cfg['maxSeconds'] <= 0:
                raise ValueError('隨機等待秒數必須大於 0。')
            if cfg['minSeconds'] > cfg['maxSeconds']:
                raise ValueError('最短秒數不能大於最長秒數。')
            settings_file = self.runtime / 'ui-settings.json'
            settings_file.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
            for ident in self.accounts:
                try:
                    self.submit(ident, lambda i=ident: self.client.call('action', {'id': i, 'action': 'config', **cfg}))
                except Exception:
                    pass
            if not silent:
                self.notice.set(f'已儲存監看設定：最短 {cfg["minSeconds"]} 秒，最長 {cfg["maxSeconds"]} 秒，目標 {cfg["count"]} 籤。')
                messagebox.showinfo('設定已儲存', f'監看秒數與設定已成功儲存！\n最短：{cfg["minSeconds"]} 秒\n最長：{cfg["maxSeconds"]} 秒\n目標籤數：{cfg["count"]} 籤', parent=self.root)
            return True
        except ValueError as e:
            if not silent:
                messagebox.showerror('設定錯誤', str(e), parent=self.root)
            return False

    def config(self):
        return {'url':self.url.get().strip(),'count':int(self.count.get()),'minSeconds':float(self.low.get()),
                'maxSeconds':float(self.high.get()),'autoResumeSoldOut':self.auto.get(),
                'entryRefresh':self.entry_refresh.get(),
                'autoRefreshInventory':self.auto_refresh_inv.get()}

    def discord_settings(self):
        from notifications import save_json, validate_webhook, spawn_notifier
        existing = getattr(self, 'discord_dialog', None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            return
        try:
            config = json.loads((self.runtime / 'discord.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            config = {}
        dialog = tk.Toplevel(self.root)
        self.discord_dialog = dialog
        dialog.title('Discord Webhook 通知設定')
        dialog.configure(bg=PANEL)
        dialog.geometry('680x560')
        dialog.resizable(False, False)
        dialog.transient(self.root)

        body = tk.Frame(dialog, bg=PANEL, padx=24, pady=20)
        body.pack(fill='both', expand=True)

        enabled = tk.BooleanVar(value=config.get('enabled', False))
        webhook = tk.StringVar(value=config.get('webhook_url', ''))
        ready = tk.BooleanVar(value='ready' in config.get('events', ['ready', 'uncertain', 'sold_out']))
        uncertain = tk.BooleanVar(value='uncertain' in config.get('events', ['ready', 'uncertain', 'sold_out']))
        sold_out = tk.BooleanVar(value='sold_out' in config.get('events', ['ready', 'uncertain', 'sold_out']))
        entry_passed = tk.BooleanVar(value='entry_passed' in config.get('events', ['ready', 'uncertain', 'sold_out', 'entry_passed']))
        ahead_enabled = tk.BooleanVar(value=config.get('ahead_threshold') is not None)
        ahead_count = tk.StringVar(value=str(config.get('ahead_threshold') if config.get('ahead_threshold') is not None else 5))
        repeat = tk.BooleanVar(value=config.get('repeat_enabled', False))
        repeat_seconds = tk.StringVar(value=str(config.get('repeat_seconds', 60)))

        tk.Checkbutton(body, text='啟用 Discord 通知', variable=enabled, bg=PANEL, fg=TEXT, selectcolor=BG,
                       activebackground=PANEL, activeforeground=TEXT, font=('Microsoft JhengHei UI', 11, 'bold')).pack(anchor='w', pady=(0, 8))

        self.label(body, 'Discord Webhook 網址（可直接按貼上）：', color=MUTED, size=10).pack(anchor='w', pady=(6, 4))

        url_row = tk.Frame(body, bg=PANEL)
        url_row.pack(fill='x', pady=(0, 10))
        entry = tk.Entry(url_row, textvariable=webhook, bg=BG, fg=TEXT, insertbackground=TEXT,
                         relief='flat', font=('Segoe UI', 10))
        entry.pack(side='left', fill='x', expand=True, ipady=7, padx=(0, 8))

        def paste_cb():
            try:
                clip = self.root.clipboard_get().strip()
                if clip: webhook.set(clip)
            except Exception: pass

        self.button(url_row, '📋 貼上', paste_cb).pack(side='left', padx=(0, 4))
        self.button(url_row, '❌ 清除', lambda: webhook.set('')).pack(side='left')

        events_frame = tk.LabelFrame(body, text=' 通知事件 ', bg=PANEL, fg=MUTED, font=('Microsoft JhengHei UI', 10), padx=12, pady=8)
        events_frame.pack(fill='x', pady=8)

        tk.Checkbutton(events_frame, text='輪到抽籤時通知（輪到你了！）', variable=ready, bg=PANEL, fg=TEXT, selectcolor=BG,
                       activebackground=PANEL, activeforeground=TEXT, font=('Microsoft JhengHei UI', 10)).pack(anchor='w', pady=2)
        tk.Checkbutton(events_frame, text='通過入場限制（進入商品頁／籤箱頁）時通知', variable=entry_passed, bg=PANEL, fg=TEXT, selectcolor=BG,
                       activebackground=PANEL, activeforeground=TEXT, font=('Microsoft JhengHei UI', 10)).pack(anchor='w', pady=2)
        tk.Checkbutton(events_frame, text='籤筒抽完（售完）時通知', variable=sold_out, bg=PANEL, fg=TEXT, selectcolor=BG,
                       activebackground=PANEL, activeforeground=TEXT, font=('Microsoft JhengHei UI', 10)).pack(anchor='w', pady=2)
        tk.Checkbutton(events_frame, text='排隊異常、需要確認時通知', variable=uncertain, bg=PANEL, fg=TEXT, selectcolor=BG,
                       activebackground=PANEL, activeforeground=TEXT, font=('Microsoft JhengHei UI', 10)).pack(anchor='w', pady=2)

        ahead_row = tk.Frame(events_frame, bg=PANEL)
        ahead_row.pack(fill='x', pady=2)
        tk.Checkbutton(ahead_row, text='前方等待人數小於或等於：', variable=ahead_enabled, bg=PANEL, fg=TEXT, selectcolor=BG,
                       activebackground=PANEL, activeforeground=TEXT, font=('Microsoft JhengHei UI', 10)).pack(side='left')
        tk.Entry(ahead_row, textvariable=ahead_count, width=6, bg=BG, fg=TEXT, insertbackground=TEXT, relief='flat').pack(side='left', padx=4, ipady=4)
        self.label(ahead_row, '人時通知', color=MUTED).pack(side='left')

        rep_row = tk.Frame(events_frame, bg=PANEL)
        rep_row.pack(fill='x', pady=2)
        tk.Checkbutton(rep_row, text='重複通知（符合條件期間，每隔：', variable=repeat, bg=PANEL, fg=TEXT, selectcolor=BG,
                       activebackground=PANEL, activeforeground=TEXT, font=('Microsoft JhengHei UI', 10)).pack(side='left')
        tk.Entry(rep_row, textvariable=repeat_seconds, width=6, bg=BG, fg=TEXT, insertbackground=TEXT, relief='flat').pack(side='left', padx=4, ipady=4)
        self.label(rep_row, '秒提醒一次，最短 10 秒）', color=MUTED).pack(side='left')

        self.label(body, '設定只儲存在這台電腦；儲存後立即生效，不會中斷排隊。', size=9, color=MUTED).pack(anchor='w', pady=(8, 12))

        actions = tk.Frame(body, bg=PANEL)
        actions.pack(fill='x', pady=(8, 0))

        def values(require_url=False):
            url = webhook.get().strip()
            if enabled.get() or require_url or url:
                url = validate_webhook(url)
            events = [name for name, var in [('ready', ready), ('uncertain', uncertain), ('sold_out', sold_out), ('entry_passed', entry_passed)] if var.get()]
            try:
                threshold = int(ahead_count.get()) if ahead_enabled.get() else None
                seconds = int(repeat_seconds.get())
            except ValueError:
                raise ValueError('等待人數與重複間隔請填整數。') from None
            if threshold is not None and not 0 <= threshold <= 100000:
                raise ValueError('等待人數需為 0～100000。')
            if not 10 <= seconds <= 86400:
                raise ValueError('重複間隔需為 10～86400 秒。')
            if enabled.get() and not events and threshold is None:
                raise ValueError('請至少選擇一種通知事件。')
            return {'enabled': enabled.get(), 'webhook_url': url, 'events': events,
                    'ahead_threshold': threshold, 'repeat_enabled': repeat.get(), 'repeat_seconds': seconds}

        def save():
            try:
                value = values()
                save_json(self.runtime / 'discord.json', value)
                spawn_notifier(self.runtime)
            except Exception as error:
                messagebox.showerror('Discord 設定', str(error), parent=dialog)
                return
            self.notice.set('Discord 設定已儲存，立即生效。')
            dialog.destroy()

        def test():
            try:
                url = values(True)['webhook_url']
            except ValueError as error:
                messagebox.showerror('Discord 設定', str(error), parent=dialog)
                return
            def send():
                import asyncio
                import aiohttp
                from notifications import send_webhook
                async def run():
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                        return await send_webhook(session, url, {'content': 'Kuji Desk：Discord Webhook 測試通知成功！', 'allowed_mentions': {'parse': []}})
                try:
                    return asyncio.run(run())
                except Exception:
                    return {'ok': False}
            self.notice.set('正在發送 Discord 測試通知…')
            self.submit('discord-test', send)

        self.button(actions, '發送測試通知', test).pack(side='left')
        self.button(actions, '儲存設定', save, primary=True, bg=GREEN, fg='#ffffff').pack(side='right')
        self.button(actions, '取消', dialog.destroy).pack(side='right', padx=8)

    def submit(self,key,function):
        if key in self.busy:return
        self.busy.add(key)
        future=self.pool.submit(function)
        future.add_done_callback(lambda result:self.results.put((key,result)))

    def drain(self):
        if self.closed:return
        while True:
            try:key,future=self.results.get_nowait()
            except queue.Empty:break
            self.busy.discard(key)
            try:
                result=future.result()
                if key=='poll':self.render(result)
                elif isinstance(result,dict) and result.get('inventoryError'):
                    message=f'帳號 {result["id"]} 籤數更新未成功：{result["inventoryError"]}（保留上次資料）'
                    self.notice.set(message)
                    if getattr(self,'log_window',None) is not None and self.log_window.winfo_exists():
                        self.add_log(result['id'],{'at':round(time.time()*1000),'message':message})
                elif key=='discord-test':
                    text='測試通知已送出。' if result.get('ok') else '測試通知未成功，請確認 Webhook 與網路連線。'
                    self.notice.set(text);messagebox.showinfo('Discord 通知',text,parent=self.root)
                elif key!='service':self.notice.set('操作完成：'+key)
            except Exception as error:
                if key=='poll':
                    self.render({'loginOnly':True, 'accounts':[]})
                else:self.notice.set(str(error));messagebox.showerror('Kuji Desk',str(error),parent=self.root)
        self.root.after(100,self.drain)

    def reload_gui(self):
        self.notice.set('正在重新整理介面與更新籤數…')
        self.batch('api_inventory')
        self.submit('poll',lambda:self.client.call(timeout=3))

    def poll(self):
        if self.closed:return
        now = time.time()
        if self.auto_refresh_inv.get() and (now - self.last_auto_inv_time >= 180):
            self.last_auto_inv_time = now
            self.batch('api_inventory')
        self.submit('poll',lambda:self.client.call(timeout=3))
        self.root.after(1000,self.poll)

    def render(self,state):
        version=state.get('version','?')
        self.service_version=version
        login_only = state.get('loginOnly', False)
        self.control_active = not login_only
        color = GREEN if login_only else RED
        self.btn_control.config(text='開啟控制台' if login_only else '關閉控制台',
                                bg=color, fg='#ffffff', activebackground=color, activeforeground='#ffffff')
        status='已連線' if version==VERSION else '舊版服務正在執行，請按右上「重新啟動服務」套用修正'
        try:
            dc=json.loads((self.runtime/'discord-status.json').read_text(encoding='utf-8'))
            discord='DC 通知已連接' if dc.get('enabled') and dc.get('connected') else 'DC 通知未連接'
        except (OSError,ValueError):discord='DC 通知未設定'
        connection = f'服務 v{version}：{status}　｜　{discord}'
        if login_only:
            connection = '控制台已關閉，可開啟專用視窗手動登入。'
            if version not in {'?', VERSION}:
                connection += ' 登入服務有新版，請按「重新啟動服務」套用。'
        self.connection.set(f'獨立介面 v{UI_VERSION}　｜　{connection}')
        self.accounts={a['id']:a for a in state.get('accounts',[])}
        self.refresh_logs()
        for ident,c in self.cards.items():
            if ident not in self.accounts:
                c['buttons']['open'].config(text='開啟／登入',state='normal' if ident not in self.busy else 'disabled')
                for action in ('monitor','inspect','requeue','restart','rename'):
                    c['buttons'][action].config(state='disabled')
                continue
            a = self.accounts[ident]
            c=self.cards[ident];c['title'].config(text=f'{ident}   '+a['label']);c['phase'].config(text='●  '+a['phaseLabel'],fg=LIME if a['phase']=='ready' else '#ffbe84' if a['phase']=='uncertain' else MUTED)
            rank='輪到你了！' if a['phase']=='ready' else f'前方 {a["queueAhead"]} 人' if a.get('queueAhead') is not None else '尚未排入隊伍'
            c['rank'].config(text=rank,font=('Microsoft JhengHei UI',25 if a.get('queueAhead') is not None or a['phase']=='ready' else 18,'bold'))
            from urllib.parse import urlparse,parse_qs
            current_id=parse_qs(urlparse(a.get('url') or '').query).get('lbdid',[''])[0]
            target=a.get('target') or {}
            box=current_id[:5] if current_id else str(target.get('seq') or '—')
            c['box'].config(text='目前視窗箱號：'+box)
            c['note'].config(text=a['note'],wraplength=max(270,c['frame'].winfo_width()-30))
            stock=a.get('inventory') or {}
            rem=stock.get('remaining')
            is_api = stock.get('source') == 'api'
            rem_str = f'{rem} 枚' if rem is not None else '—'
            c['stock'].config(text=f'剩餘籤數：{rem_str}',fg='#ff6b6b' if rem==0 else LIME if rem is not None else MUTED,font=('Microsoft JhengHei UI',36,'bold'))
            stock_key=json.dumps(stock.get('prizes',[]),sort_keys=True)
            if stock_key!=c['stock_key']:
                c['stock_key']=stock_key
                c['tree'].delete(*c['tree'].get_children())
                for i,prize in enumerate(stock.get('prizes',[])):
                    c['tree'].insert('', 'end',values=(prize['label'],f'{prize["remaining"]} / {prize["total"]}'),tags=('zero' if prize['remaining']==0 else 'even' if i%2==0 else 'odd',))
            if is_api:
                c['updated'].config(text='已更新 '+stamp(stock.get('readAt')),fg=LIME)
            else:
                c['updated'].config(text='頁面讀取 '+stamp(stock.get('readAt')),fg=MUTED)
            is_monitoring = bool(a.get('canStop'))
            c['buttons']['monitor'].config(
                text='停止監看' if is_monitoring else '開始監看',
                bg=RED if is_monitoring else GREEN,
                fg='#ffffff',
                activebackground=RED if is_monitoring else GREEN,
                activeforeground='#ffffff',
                font=('Microsoft JhengHei UI',10,'bold')
            )
            c['buttons']['open'].config(text='切回視窗' if a.get('opened') else ('開啟視窗' if a.get('hasSession') else '開啟／登入'))
            enabled={'open':True,'monitor':a.get('canStart') or a.get('canStop'),
                     'inspect':a.get('canInspect'),
                     'requeue':not login_only and a.get('opened') and a['phase'] not in {'watching','opening','submitting','leaving'},
                     'restart':not login_only,
                     'rename':True}
            for action,b in c['buttons'].items():b.config(state='normal' if enabled[action] and ident not in self.busy else 'disabled')

    def act(self,ident,action):
        if action=='api_inventory':
            def refresh_selected_box():
                current=next((a for a in self.client.call()['accounts'] if a['id']==ident),{})
                if not current.get('canRefresh') or current.get('phase') in {'watching','opening','leaving'}:
                    return {'skipped':True}
                try:
                    return self.client.call('action',{'id':ident,'action':'api_inventory'})
                except Exception as error:
                    return {'inventoryError':str(error),'id':ident}
            self.submit(ident,refresh_selected_box)
            return
        if action=='monitor':action='stop' if self.accounts.get(ident,{}).get('canStop') else 'start'
        if action=='rename':
            self.rename(ident)
            return
        if self.service_version != VERSION and action in {'requeue','inspect','restart','navigate','api_inventory'}:
            messagebox.showinfo('套用修正','目前背景服務仍是舊版。請先按右上「重新啟動服務」套用修正；可能中斷目前隊伍。',parent=self.root)
            return
        confirms={'requeue':'會依目前視窗退出或返回列表，放棄原順位，再開始找新滿箱。只影響此帳號。',
                  'restart':'會關閉並重開此帳號的專用視窗，可能中斷此帳號隊伍。登入資料保留，其他帳號不變。',
                  'reset':'只清除助手任務，不會替你退出網站隊伍。確認已完成或退出隊伍？'}
        if action in confirms and not messagebox.askyesno('確認操作',confirms[action],parent=self.root):return
        try:
            config = self.config()
        except ValueError:
            if action != 'open' or self.control_active:
                messagebox.showerror('設定','請輸入正確籤數與秒數。',parent=self.root)
                return
            config = {}
        data = {**config, 'id':ident, 'action':action, 'confirmed':True}
        def send_action():
            if action == 'open':
                self.client.ensure_server(login_only=True)
            return self.client.call('action', data)
        self.submit(ident, send_action)

    def batch(self,action):
        if action == 'start': self.save_settings(silent=True)
        if action == 'api_inventory':
            selected=[]
            for ident,a in self.accounts.items():
                if a.get('canRefresh') and a.get('phase') not in {'watching','opening','leaving'} and ident not in self.busy:
                    selected.append(ident);self.act(ident,'api_inventory')
            self.notice.set('正在以 API 查詢帳號：'+ '、'.join(selected) if selected else '尚未選定箱子的帳號已略過，監看繼續。')
            return
        key={'start':'canStart','stop':'canStop','inventory':'canRefresh'}[action]
        selected=[]
        for ident,a in self.accounts.items():
            if a.get(key) and ident not in self.busy:
                selected.append(ident);self.act(ident,action)
        if action=='inventory':
            self.notice.set('正在以 F5 更新帳號：'+ '、'.join(selected) if selected else '目前沒有可更新的箱子頁面；請先開啟帳號的箱子視窗。')

    def restart_service(self):
        current = self.client.alive()
        if not current:
            self.notice.set('目前沒有本機服務需要重新啟動。')
            return
        if messagebox.askyesno('重新啟動整體服務','這會套用新版修正並重啟總控。三個專用視窗可能關閉、隊伍可能中斷；登入與設定會保留。要繼續嗎？',parent=self.root):
            self.submit('service',self.client.restart_server)
            self.notice.set('正在重新啟動服務，請稍候…')

    def rename(self,ident):
        label=simpledialog.askstring('帳號名稱','輸入此帳號的顯示名稱：',initialvalue=self.accounts.get(ident,{}).get('label',ident),parent=self.root)
        if label:self.submit(ident,lambda:self.client.call('action',{'id':ident,'action':'label','label':label}))

    def show_logs(self):
        existing = getattr(self, 'log_window', None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            return
        dialog = tk.Toplevel(self.root)
        self.log_window = dialog
        dialog.title('搶箱與排隊執行紀錄')
        dialog.geometry('1000x560')
        dialog.configure(bg=PANEL)
        self.label(dialog, '選擇籤筒查看歷史 · 每頁最近 500 筆 · 自動更新', color=MUTED).pack(anchor='w',padx=12,pady=10)
        tabs = ttk.Notebook(dialog)
        tabs.pack(fill='both',expand=True,padx=12,pady=10)
        self.log_trees = {}
        self.log_records = {i:[] for i in 'ABC'}
        self.log_filters = {}
        self.log_loading = True
        self.log_seen = {i:set() for i in 'ABC'}
        for ident in 'ABC':
            frame=tk.Frame(tabs,bg=PANEL)
            tabs.add(frame,text=ident+' · '+self.accounts.get(ident,{}).get('label',ident))
            toolbar=tk.Frame(frame,bg=PANEL);toolbar.pack(fill='x',pady=6)
            choice=ttk.Combobox(toolbar,state='readonly',values=['全部紀錄'])
            choice.set('全部紀錄');choice.pack(side='left',fill='x',expand=True)
            self.log_filters[ident]=choice
            choice.bind('<<ComboboxSelected>>',lambda e,i=ident:self.draw_logs(i))
            self.button(toolbar,'上一個籤筒',lambda i=ident:self.previous_box_log(i)).pack(side='left',padx=6)
            tree=ttk.Treeview(frame,columns=('time','message'),show='headings')
            tree.heading('time',text='時間');tree.heading('message',text='步驟／結果／耗時')
            tree.column('time',width=170,stretch=False);tree.column('message',width=760)
            scroll=ttk.Scrollbar(frame,orient='vertical',command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)
            scroll.pack(side='right',fill='y');tree.pack(fill='both',expand=True)
            self.log_trees[ident]=tree
            try:
                with (self.runtime/f'events-{ident}.jsonl').open(encoding='utf-8') as stream:
                    for line in stream:
                        try:self.add_log(ident,json.loads(line))
                        except (ValueError,KeyError,TypeError):pass
            except OSError:pass
        self.log_loading = False
        self.refresh_logs()
        for ident in 'ABC':self.draw_logs(ident)

    @staticmethod
    def log_box_label(event):
        if not event.get('boxId'):return '未分類／尚未選箱'
        box = f'BOX-{event["boxSeq"]:05d}' if event.get('boxSeq') is not None else 'BOX-'+event['boxId'][:5]
        return f'{box} · {event.get("pid") or "商品未知"} · {event["boxId"]}'

    def add_log(self,ident,event):
        key=(event['at'],event['message'])
        if key in self.log_seen[ident]:return
        self.log_seen[ident].add(key)
        self.log_records[ident].append(event)
        if not self.log_loading:self.draw_logs(ident)

    def draw_logs(self,ident):
        records=self.log_records[ident]
        labels=list(dict.fromkeys(self.log_box_label(e) for e in reversed(records)))
        choice=self.log_filters[ident]
        choice.configure(values=['全部紀錄']+labels)
        selected=choice.get()
        rows=[e for e in records if selected=='全部紀錄' or self.log_box_label(e)==selected][-500:]
        tree=self.log_trees[ident]
        tree.delete(*tree.get_children())
        for event in rows:
            at=event['at']
            label=time.strftime('%m-%d %H:%M:%S',time.localtime(at/1000))+f'.{at%1000:03d}'
            tree.insert('', 'end',values=(label,event['message']))
        if tree.get_children():tree.see(tree.get_children()[-1])

    def previous_box_log(self,ident):
        labels=list(dict.fromkeys(self.log_box_label(e) for e in reversed(self.log_records[ident]) if e.get('boxId')))
        current=(self.accounts.get(ident,{}).get('target') or {}).get('id')
        previous=next((label for label in labels if not current or not label.endswith(' · '+current)),None)
        if previous:
            self.log_filters[ident].set(previous);self.draw_logs(ident)
        else:self.notice.set('目前沒有可辨識的上一個籤筒紀錄；舊紀錄可在「全部紀錄」查看。')

    def refresh_logs(self):
        dialog=getattr(self,'log_window',None)
        if dialog is None or not dialog.winfo_exists():return
        for ident,a in self.accounts.items():
            for event in a.get('events',[]):self.add_log(ident,event)

    def toggle_control(self):
        alive = self.client.alive()
        if alive and not alive.get('loginOnly'):
            if messagebox.askyesno('關閉控制台', '確定要關閉控制台服務嗎？\n專用視窗與隊伍連線將會中斷，登入與設定會完整保留。', parent=self.root):
                try:
                    self.client.call('control', {'action': 'shutdown', 'confirmed': True})
                except Exception:
                    try:
                        self.client.stop_legacy_server()
                    except Exception:
                        pass
                self.notice.set('正在關閉控制台服務…')
                self.render({'loginOnly':True, 'accounts':[]})
        else:
            self.notice.set('正在啟動控制台服務…')
            def start_srv():
                try:
                    self.client.ensure_server()
                    self.notice.set('控制台服務已啟動。')
                except Exception as e:
                    self.notice.set(f'啟動失敗：{e}')
            self.submit('service', start_srv)

    def close(self):
        self.closed=True;self.pool.shutdown(wait=False,cancel_futures=True);self.root.destroy()

    def run(self):self.root.mainloop()
