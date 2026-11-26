"""Local three-profile Kuji manager. No extension, credential export or automatic purchases."""
import argparse
import asyncio
import html
import json
import os
from pathlib import Path
from email.utils import parsedate_to_datetime
import random
import re
import secrets
import subprocess
import time
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser
from urllib.request import Request, urlopen

import aiohttp
from aiohttp import web
import aiohttp
from bs4 import BeautifulSoup
import shutil
import sys

HERE = Path(__file__).resolve().parent
CHECKOUT_RUNTIME = HERE.parents[1] / 'Runtime' / 'kuji-manager'
DEFAULT_RUNTIME = Path(os.environ.get('KUJI_RUNTIME', str(
    CHECKOUT_RUNTIME if (HERE.parents[1] / 'AGENTS.md').exists()
    else Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'KujiDesk')))

def ensure_playwright_node():
    if os.environ.get('PLAYWRIGHT_NODEJS_PATH'): return
    candidates = []
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        candidates.append(Path(sys._MEIPASS) / 'playwright' / 'driver' / 'node.exe')
    candidates.append(CHECKOUT_RUNTIME / 'venv' / 'Lib' / 'site-packages' / 'playwright' / 'driver' / 'node.exe')
    sys_node = shutil.which('node')
    if sys_node: candidates.append(Path(sys_node))
    candidates.append(Path(r'C:\Program Files\nodejs\node.exe'))
    for c in candidates:
        if c and Path(c).is_file(): os.environ['PLAYWRIGHT_NODEJS_PATH'] = str(Path(c).resolve()); return
ensure_playwright_node()

from playwright.async_api import async_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
from details import parse_detail_text, parse_detail_html, READ_DETAIL
from notifications import spawn_notifier
from cloudflare_pause import requires_cloudflare_verification
from service_runtime import bind_listener, remember_runtime

# (Runtime path defined above)
# 版本的唯一來源。build_exe.py 用它組出分享資料夾名稱，狀態 API 也回報這個值。
# 升版只改這裡與 native_ui.py 的 VERSION／UI_VERSION。
VERSION = '1.5.38'
ORIGIN = 'https://on-line.1kuji.com'
LIST_PATH = '/Form/Product/SelectBox.aspx'
DETAIL_PATH = '/Form/Product/SelectBoxDetail.aspx'
FETCH_BOX_HTML = """async (url) => {
    if (location.href !== url) throw new Error('分頁網址已變更');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
        const response = await fetch(url, {
            credentials: 'include',
            cache: 'no-store',
            signal: controller.signal
        });
        return {
            status: response.status,
            url: response.url,
            headers: { 'cf-mitigated': response.headers.get('cf-mitigated') || '' },
            html: await response.text()
        };
    } finally {
        clearTimeout(timeout);
    }
}"""
ACTIVE = {'watching', 'opening', 'submitting', 'waiting', 'ready', 'uncertain', 'leaving'}
FETCH_QUEUE_JSON = r'''async (expectedUrl) => {
    if (location.href !== expectedUrl) throw new Error('分頁網址已變更');
    const user = document.documentElement.innerHTML.match(/userId\s*:\s*['"]([^'"]{1,80})['"]/);
    if (!user) throw new Error('頁面未提供查詢身分');
    const url = new URL(location.href);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
        const response = await fetch(url.origin + url.pathname + '/GetLotteryBoxWaitCount', {
            method: 'POST', credentials: 'include', cache: 'no-store', signal: controller.signal,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({userId:user[1], productId:url.searchParams.get('pid'),
                                  hashedDisplayId:url.searchParams.get('lbdid')})
        });
        return {status:response.status, url:response.url,
                headers:{'cf-mitigated':response.headers.get('cf-mitigated') || ''},
                text:await response.text()};
    } finally { clearTimeout(timeout); }
}'''
LABELS = {'closed':'未開啟', 'idle':'待命', 'watching':'監看新箱', 'opening':'開啟箱子',
          'recovering':'等待入場', 'leaving':'退出並重排中', 'submitting':'已觸發排隊', 'waiting':'已確認排隊', 'ready':'輪到你了', 'uncertain':'需要確認'}


def now():
    return round(time.time() * 1000)


def list_url(value):
    u = urlparse(html.unescape(str(value).strip()))
    q = parse_qs(u.query)
    pid = q.get('pid', [''])[0]
    if u.scheme != 'https' or u.netloc != 'on-line.1kuji.com' or u.path != LIST_PATH or not re.fullmatch(r'[A-Za-z0-9_]{1,80}', pid):
        raise ValueError('請貼上一番賞的選箱列表網址，需包含 pid。')
    page = q.get('pno', ['1'])[0]
    if not page.isdigit() or not 1 <= int(page) <= 9999:
        raise ValueError('選箱頁碼無效。')
    return ORIGIN + LIST_PATH + '?' + urlencode({'pid':pid, 'pno':page}), pid


def entry_url(value):
    value = html.unescape(str(value or ORIGIN).strip())
    u = urlparse(value)
    if u.scheme != 'https' or u.netloc != 'on-line.1kuji.com' or u.path not in {'', '/', LIST_PATH, '/Form/Product/ProductDetail.aspx', '/Form/Product/ProductList.aspx'}:
        raise ValueError('請貼上一番賞首頁、商品頁或選箱列表網址。')
    pid = parse_qs(u.query).get('pid',[''])[0]
    if pid and not re.fullmatch(r'[A-Za-z0-9_]{1,80}',pid):
        raise ValueError('商品PID格式無效。')
    if u.path == LIST_PATH and pid:return list_url(value)
    return u._replace(fragment='').geturl(), pid or None


def entry_limited(text):
    return '一時的に入場いただける人数を制限しております' in re.sub(r'\s+', '', text or '')


def detail_url(pid, target):
    return ORIGIN + DETAIL_PATH + '?' + urlencode({'shop':'0', 'pid':pid, 'lbdid':target['id'], 'sort':'', 'fil':'', 'udns':'', 'pno':'1'})


def parse_boxes(text):
    soup = BeautifulSoup(text, 'html.parser')
    boxes = []
    for item in soup.select('.selectbox__box-list-item'):
        link = item.select_one('a[class*="BOX-"]')
        amount = item.select_one('.selectbox__text--product-amount')
        waiting = item.select_one('.selectbox__text--product-waiting')
        classes = ' '.join(link.get('class', [])) if link else ''
        seq = re.search(r'(?:^|\s)BOX-(\d+)(?:\s|$)', classes)
        ident = re.search(r'(?:^|\s)([0-9A-F]{16})(?:\s|$)', classes, re.I)
        count = re.search(r'残\s*(\d+)\s*枚', amount.get_text()) if amount else None
        people = re.search(r'(\d+)\s*人', waiting.get_text()) if waiting else None
        if seq and ident and count:
            boxes.append({'seq':int(seq[1]), 'id':ident[1].upper(), 'amount':int(count[1]), 'waiting':int(people[1]) if people else None})
    if not boxes:
        page_text = soup.get_text(' ', strip=True)
        if (not soup.select_one('input[type="password"]') and 'くじ箱選択' in page_text
                and (soup.select_one('.selectbox__box-list') is not None
                     or re.search(r'くじ箱(?:がありません|はありません|が存在しません)', page_text))):
            return []
        raise ValueError('未讀到箱子。請檢查登入、驗證或網站訊息；監看已停止。')
    return boxes


def select_box(boxes, baseline, count):
    choices = [b for b in boxes if b['seq'] > baseline and b['amount'] == count]
    return min(choices, key=lambda b:(b['waiting'] if b['waiting'] is not None else float('inf'), -b['seq'])) if choices else None


def validate_config(data):
    url, pid = entry_url(data.get('url', ''))
    count = int(data.get('count', 70))
    low, high = float(data.get('minSeconds', 2.2)), float(data.get('maxSeconds', 4.5))
    if not 1 <= count <= 1000 or not 2.2 <= low <= high <= 300:
        raise ValueError('張數需為 1–1000，隨機間隔需為 2.2–300 秒且最短不大於最長。')
    return {'url':url, 'pid':pid, 'count':count, 'minSeconds':low, 'maxSeconds':high,
            'autoResumeSoldOut':bool(data.get('autoResumeSoldOut', True)),
            'entryRefresh':bool(data.get('entryRefresh', True))}


class CloudflarePaused(ValueError):
    pass


class Account:
    def __init__(self, manager, ident):
        self.manager, self.id = manager, ident
        self.label = f'帳號 {ident}'
        self.chrome_profile_directory = None
        self.profile_context_id = None
        self.context = self.page = self.task = None
        self.http_session: 'aiohttp.ClientSession | None' = None
        self.user_id: 'str | None' = None
        self.lock = asyncio.Lock()
        self.phase, self.note = 'closed', '開啟獨立視窗後，手動登入此帳號。'
        self.config, self.target, self.metrics = {}, None, {}
        self.queue_no = None
        self.soldout_task = None
        self.soldout_attempt = None
        self.queue_alert = False
        self.queue_reason = None
        self.soldout_acknowledged = False
        self.queue_ahead = None
        self.inventory = {}
        self.exit_available = self.refresh_available = False
        self.events = []
        self.next_check = None
        self.entry_pending = False
        self.cloudflare_paused = False
        self.entry_cooldown_until = 0.0
        self.entry_passed_at = None
        self.cancel = asyncio.Event()
        self.journal = manager.runtime / f'job-{ident}.json'
        if self.journal.exists():
            try:
                saved = json.loads(self.journal.read_text(encoding='utf-8'))
                self.config = saved.get('config', {})
                self.label = saved.get('label', self.label)
                self.chrome_profile_directory = saved.get('chromeProfile')
                if saved.get('phase') in ACTIVE:
                    self.phase = 'uncertain'
                    self.target, self.metrics = saved.get('target'), saved.get('metrics', {})
                    self.note = '上次任務未結束：不會自動重送。請先確認網站排隊狀態。'
            except (ValueError, OSError):
                self.phase, self.note = 'uncertain', '上次紀錄無法讀取，請確認網站狀態後結束本次任務。'

    def persist(self):
        value = {'phase':self.phase, 'label':self.label, 'config':self.config, 'target':self.target, 'metrics':self.metrics, 'chromeProfile':self.chrome_profile_directory}
        temp = self.journal.with_suffix('.tmp')
        with temp.open('w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        temp.replace(self.journal)

    def event(self, message):
        record = {'at':now(), 'message':message, 'pid':self.config.get('pid'),
                  'boxId':(self.target or {}).get('id'), 'boxSeq':(self.target or {}).get('seq')}
        self.events.append(record)
        self.events = self.events[-500:]
        try:
            with (self.manager.runtime / f'events-{self.id}.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + '\n')
        except OSError:
            pass

    def state(self):
        opened = self.page is not None and not self.page.is_closed()
        has_session = bool(self.http_session and not self.http_session.closed)
        page_url = urlparse(self.page.url) if opened else None
        if self.manager.login_only:
            phase = 'idle' if opened else 'closed'
            return {'id':self.id, 'label':self.label, 'phase':phase,
                    'phaseLabel':'僅供登入' if opened else LABELS[phase], 'opened':opened,
                    'note':self.note if opened and self.phase == 'idle' else '背景服務已關閉，可手動登入獨立視窗。',
                    'events':self.events[-500:]}
        if opened and not self.cloudflare_paused and self.phase == 'uncertain' and (not self.task or self.task.done()) and not getattr(self, '_healing', False):
            self._healing = True
            asyncio.create_task(self._auto_heal_uncertain())
        if (opened and self.phase=='idle' and self.entry_pending and not self.lock.locked()
                and (not self.task or self.task.done()) and not self.manager.shutting_down):
            self.task=asyncio.create_task(self.recover_entry())
        return {'id':self.id, 'label':self.label, 'phase':self.phase, 'phaseLabel':LABELS[self.phase],
                'note':self.note, 'opened':opened, 'hasSession':has_session,
                'target':self.target, 'queueNo':self.queue_no,
                'metrics':self.metrics, 'inventory':self.inventory, 'queueAhead':self.queue_ahead, 'soldOut':self.queue_reason == 'SoldOut' or (self.inventory.get('remaining') == 0 if self.inventory else False),
                'canRequeue':opened and self.phase in {'idle','waiting','ready','uncertain'},
                'canRestart':True,
                'canInspect':opened and self.phase not in {'opening','submitting','leaving'},
                'canRefresh':opened and not self.cloudflare_paused and self.phase not in {'watching','opening','submitting','leaving'}
                    and page_url and page_url.netloc == 'on-line.1kuji.com' and page_url.path == DETAIL_PATH,
                'events':self.events[-500:], 'config':self.config,
                'nextCheckAt':self.next_check, 'url':self.page.url if opened else None,
                'canStart':(has_session or opened) and self.phase in {'idle','closed'},
                'canStop':self.phase in {'watching','recovering'} or self.entry_pending, 'canReset':self.phase in {'uncertain','ready','waiting'}, 'entryPassedAt':self.entry_passed_at}



    async def sync_cookies(self):
        # The attached browser owns authentication and all website requests.
        return

    async def pick_chrome_page(self, browser, choose=False, directory=None):
        if self.manager.picker_lock.locked():
            raise ValueError('另一張帳號卡片正在綁定，請稍候。')
        directory = directory or (None if choose else self.chrome_profile_directory)
        if not isinstance(directory, str) or not directory or '/' in directory or '\\' in directory or directory in {'.','..'}:
            raise ValueError('請先在主視窗選擇並確認 Chrome 設定檔。')
        async with self.manager.picker_lock:
            self.note = '正在辨識已開啟 Chrome 視窗的設定檔。'
            self.event(self.note)
            candidates = {}
            for context in browser.contexts:
                for page in list(context.pages):
                    if page.is_closed():
                        continue
                    session = await context.new_cdp_session(page)
                    try:
                        info = (await session.send('Target.getTargetInfo'))['targetInfo']
                    except PlaywrightError:
                        if page.is_closed():
                            continue
                        raise
                    finally:
                        await session.detach()
                    profile_id = info.get('browserContextId')
                    if profile_id and profile_id not in candidates:
                        candidates[profile_id] = (context,page)
            selected = None
            for profile_id, (context,page) in candidates.items():
                known = self.manager.profile_directories.get(profile_id)
                if known is None:
                    probe = await self.new_entry_page(parent_page=page, parent_context=context,
                                                      expected_profile=profile_id)
                    try:
                        await probe.goto('chrome://version/', wait_until='domcontentloaded', timeout=10000)
                        profile_path = (await probe.locator('#profile_path').inner_text(timeout=5000)).strip()
                        known = Path(profile_path).name
                        self.manager.profile_directories[profile_id] = known
                    finally:
                        await probe.close()
                if known == directory:
                    selected = profile_id, context, page
                    break
            if selected is None:
                raise ValueError('未找到所選設定檔的可連接視窗。請先開啟該 Chrome 設定檔的一番賞分頁，並允許遠端偵錯。')
            profile_id, context, page = selected
            if any(a is not self and (a.profile_context_id == profile_id or a.chrome_profile_directory == directory)
                   for a in self.manager.accounts.values()):
                raise ValueError('這個設定檔已綁定另一張帳號卡片。')
            site_pages = []
            for candidate_context in browser.contexts:
                for candidate in list(candidate_context.pages):
                    if candidate.is_closed() or urlparse(candidate.url).netloc != 'on-line.1kuji.com':
                        continue
                    session = await candidate_context.new_cdp_session(candidate)
                    try:
                        info = (await session.send('Target.getTargetInfo'))['targetInfo']
                    finally:
                        await session.detach()
                    if info.get('browserContextId') == profile_id:
                        site_pages.append((candidate_context,candidate))
            if len(site_pages) > 1:
                raise ValueError('此設定檔有多個一番賞分頁，請保留要交給助手的一頁再綁定。')
            if site_pages:
                context, page = site_pages[0]
            else:
                page = await self.new_entry_page(parent_page=page, parent_context=context,
                                                 expected_profile=profile_id)
                await page.goto(ORIGIN, wait_until='commit', timeout=30000)
            session = await context.new_cdp_session(page)
            try:
                window = await session.send('Browser.getWindowForTarget')
            finally:
                await session.detach()
            self.chrome_profile_directory = directory
            return window['windowId'], profile_id, context, page

    async def open(self, data):
        browser = self.manager.attached_browser
        if browser is not None and not browser.is_connected():
            self.manager.browser_disconnected(browser)
        if self.page and not self.page.is_closed() and not data.get('chooseProfile'):
            try:
                await asyncio.wait_for(self.focus_window(), timeout=8)
                return
            except (PlaywrightError, TimeoutError):
                await self.cancel_observer()
                if self.page:
                    self.page.remove_listener('close', self.on_closed)
                    self.page.remove_listener('websocket', self.watch_socket)
                    self.page = None
        config = None if self.manager.login_only else validate_config(data)
        async with self.manager.browser_lock:
            browser = self.manager.attached_browser
            if browser is None or not browser.is_connected():
                self.note = '正在連接 Chrome，請查看 Chrome 的允許連線提示（最多等待60秒）。'
                self.event(self.note)
                self.persist()
                try:
                    browser = await self.manager.playwright.chromium.connect_over_cdp('chrome', timeout=60000)
                except PlaywrightError as error:
                    self.note = 'Chrome 連線未完成。請確認遠端偵錯已啟用，並在 Chrome 按允許後重新連接。'
                    self.event(self.note+' 錯誤類型：'+type(error).__name__)
                    self.persist()
                    raise ValueError(self.note) from error
                self.manager.attached_browser = browser
                browser.on('disconnected', lambda *_: self.manager.browser_disconnected(browser))
        window_id, profile_id, context, page = await self.pick_chrome_page(browser, choose=bool(data.get('chooseProfile')), directory=data.get('profileDirectory'))
        if self.context and hasattr(self, 'context_close_callback'):
            self.context.remove_listener('close', self.context_close_callback)
        if self.page:
            self.page.remove_listener('close', self.on_closed)
            self.page.remove_listener('websocket', self.watch_socket)
        self.profile_context_id = profile_id
        self.context, self.page = context, page
        self.cancel.clear()
        self.entry_pending = False
        self.context_close_callback = lambda *_: self.on_context_closed(context)
        context.on('close', self.context_close_callback)
        page.on('close', self.on_closed)
        page.on('websocket', self.watch_socket)
        if config is not None:
            self.config = config
        if self.phase == 'closed':
            self.phase = 'idle'
        self.note = '已綁定 Chrome 設定檔 '+self.chrome_profile_directory+'，可切回視窗確認登入。'
        self.persist()
        self.event(self.note)
        await page.bring_to_front()

    async def focus_window(self):
        if not self.page or self.page.is_closed():
            raise ValueError('請先開啟獨立視窗。')
        await self.page.bring_to_front()

    def on_context_closed(self, context):
        if self.context is not context:
            return
        self.context = self.page = None
        self.entry_pending = False
        self.on_closed()

    def on_closed(self, *_):
        self.cancel.set()
        if self.phase in {'opening', 'submitting', 'leaving'}:
            self.phase, self.note = 'uncertain', '獨立視窗已關閉，排隊可能中斷；請人工確認，不會自動重送。'
        elif self.phase in {'waiting', 'ready'}:
            # API polling loop will keep running; don't downgrade to uncertain yet.
            self.note = '獨立視窗已關閉，順位更新已停止。請重新開啟並確認網站狀態。'
        elif self.phase not in {'uncertain'}:
            self.phase, self.note = 'closed', '獨立視窗已關閉。'
        self.persist()
        self.event(self.note)

    def watch_socket(self, socket):
        if socket.url == 'wss://on-line.1kuji.com/_webapi/LotteryBoxQueue':
            socket.on('framereceived', self.socket_message)

    def socket_message(self, payload):
        # Passive observation only: never send WebSocket messages ourselves.
        try:
            data = json.loads(payload)
        except (ValueError, TypeError):
            return
        if self.manager.login_only or self.phase not in {'submitting','waiting','ready','uncertain'}:
            return
        if not isinstance(data, dict):
            return
        action = data.get('Action')
        if action == 'YourTurn':
            self.signal_ready()
        elif action in {'Close','SoldOut','TimeUp','EndViewing'}:
            self.queue_reason = action
            self.queue_alert = True
            self.phase, self.note = 'uncertain', f'網站通知 {action}，請切回視窗確認。'
            self.persist()
            self.event(self.note)

    def signal_ready(self):
        if self.phase == 'ready':
            return
        self.phase, self.note = 'ready', '輪到你了，請切回獨立視窗手動繼續。'
        self.metrics['readyAt'] = now()
        self.persist()
        self.event('輪到你了')

    def check_cloudflare(self, text='', response=None, headers=None):
        headers = headers if headers is not None else getattr(response, 'headers', None)
        if not requires_cloudflare_verification(text, headers):
            return
        if not self.cloudflare_paused:
            self.cloudflare_paused = True
            self.entry_pending = False
            self.cancel.set()
            self.phase = 'uncertain' if self.target else 'idle'
            # shortcut: 這句必須與 notifications.py 的 CLOUDFLARE_NOTICE 完全一致，
            # 否則 Cloudflare 通知的比對會失效；兩邊要一起改，未來應抽成共用常數。
            self.note = 'Cloudflare 要求真人驗證，自動監看已暫停。'
            self.persist()
            self.event(self.note)
        raise CloudflarePaused(self.note)

    async def wait_temporary_page(self, entry_only=False, page=None):
        """Retry only a temporary error page, never an established queue."""
        page = page if page is not None else self.page
        recovered = False
        attempt = 0
        while True:
            if self.cancel.is_set():raise asyncio.CancelledError()
            text = await page.locator('body').inner_text()
            self.check_cloudflare(text)
            normal = await page.locator(
                'a[class*="BOX-"], a.waitingStart, [id$="_lbExitQueue"]').count()
            product = urlparse(page.url).path == '/Form/Product/ProductDetail.aspx'
            gate = entry_limited(text)
            if not gate and (normal or 'あなたの番です' in text or '一時的' not in text or (product and await page.locator('h1, h2').count())):
                current=urlparse(page.url)
                if entry_only and (current.netloc!='on-line.1kuji.com' or current.path not in {LIST_PATH,'/Form/Product/ProductDetail.aspx'}):
                    self.note='等待登入或選擇商品；到達商品頁／選箱頁後自動接續。'
                    await asyncio.sleep(1)
                    continue
                if recovered:
                    self.entry_passed_at = now()
                return recovered
            if gate and not self.config.get('entryRefresh', True):
                self.note = '網站暫時限制入場；已關閉自動入場刷新，請手動操作。'
                self.event(self.note)
                return False
            recovered = True
            attempt += 1
            self.note = f'網站暫時限制存取，等待隨機間隔後重試（第 {attempt} 次，可按停止）。'
            self.event(self.note)
            await self.navigate_entry_page(page)

    async def navigate_entry_page(self, page, url=None):
        # Tabs choose independent delays; only server-requested cooldown is shared.
        delay=random.uniform(self.config.get('minSeconds',2.2),self.config.get('maxSeconds',4.5))
        await asyncio.sleep(delay)
        while self.entry_cooldown_until>time.monotonic():
            until=self.entry_cooldown_until
            await asyncio.sleep(max(0,until-time.monotonic()))
            if self.entry_cooldown_until<=until:break
        if self.cancel.is_set():raise asyncio.CancelledError()
        response=await page.goto(url,wait_until='domcontentloaded',timeout=30000) if url else await page.reload(wait_until='domcontentloaded',timeout=30000)
        self.check_cloudflare(response=response)
        if response and response.status in {429,503}:
            retry=response.headers.get('retry-after','')
            try:
                seconds=float(retry) if retry.isdigit() else parsedate_to_datetime(retry).timestamp()-time.time()
            except (TypeError,ValueError,OverflowError):
                seconds=30
            self.entry_cooldown_until=max(self.entry_cooldown_until,time.monotonic()+max(0,seconds))
            self.event('網站要求冷卻，所有入場分頁一起等待')
        return response

    async def new_entry_page(self, parent_page=None, parent_context=None, expected_profile=None):
        parent_page = parent_page if parent_page is not None else self.page
        parent_context = parent_context if parent_context is not None else self.context
        expected_profile = expected_profile if expected_profile is not None else self.profile_context_id
        marker = 'about:blank#kuji-entry-'+secrets.token_hex(16)
        session = await parent_context.new_cdp_session(parent_page)
        try:
            parent = (await session.send('Target.getTargetInfo'))['targetInfo']
            if parent.get('browserContextId') != expected_profile:
                raise ValueError('目前分頁已不是原帳號的 Chrome 設定檔。')
            opened = await session.send('Runtime.evaluate', {
                'expression':'window.open('+json.dumps(marker)+', "_blank") !== null',
                'userGesture':True, 'returnByValue':True})
            if not opened.get('result', {}).get('value'):
                raise ValueError('Chrome 未能開啟入場分頁。')
            for _ in range(50):
                for context in self.manager.attached_browser.contexts:
                    for page in context.pages:
                        if page.url != marker:
                            continue
                        child = await context.new_cdp_session(page)
                        try:
                            info = (await child.send('Target.getTargetInfo'))['targetInfo']
                        finally:
                            await child.detach()
                        if info.get('browserContextId') != expected_profile:
                            raise ValueError('新增分頁的登入設定檔不符，已停止。')
                        return page
                await asyncio.sleep(.1)
            raise ValueError('未能取得新增的入場分頁。')
        except BaseException:
            try:
                targets = (await session.send('Target.getTargets'))['targetInfos']
                for target in targets:
                    if target.get('url') == marker:
                        await session.send('Target.closeTarget', {'targetId':target['targetId']})
            except PlaywrightError:
                pass
            raise
        finally:
            await session.detach()

    async def wait_entry_tabs(self):
        original=self.page
        source=original.url
        expected_pid=parse_qs(urlparse(source).query).get('pid',[''])[0]
        extras=[];tasks=[];winner=None
        async def candidate(page, fresh=False):
            if fresh:await self.navigate_entry_page(page,source)
            await self.wait_temporary_page(entry_only=bool(expected_pid),page=page)
            current=urlparse(page.url)
            if current.netloc!='on-line.1kuji.com':
                raise ValueError('入場分頁未停留在 1kuji 網域。')
            if expected_pid:
                pid=parse_qs(current.query).get('pid',[''])[0]
                if (current.path not in {LIST_PATH,'/Form/Product/ProductDetail.aspx'}
                        or not re.fullmatch(r'[A-Za-z0-9_]{1,80}',pid) or pid!=expected_pid):
                    raise ValueError('入場分頁未進入同商品頁，未接續排隊。')
            return page
        try:
            for _ in range(4):
                if self.cancel.is_set():raise asyncio.CancelledError()
                extras.append(await self.new_entry_page())
            self.event('已建立同帳號5個入場分頁，各自隨機抖動刷新')
            tasks=[asyncio.create_task(candidate(original))]+[asyncio.create_task(candidate(p,True)) for p in extras]
            pending=set(tasks)
            while pending:
                done,pending=await asyncio.wait(pending,return_when=asyncio.FIRST_COMPLETED)
                for task in tasks:
                    if task not in done or task.cancelled():continue
                    try:winner=task.result()
                    except CloudflarePaused:
                        raise
                    except Exception as error:
                        self.event('入場分頁失敗：'+type(error).__name__)
                        continue
                    break
                if winner is not None:break
            if winner is None:raise ValueError('所有入場分頁均未成功，請查看網站狀態。')
            if self.cancel.is_set():raise asyncio.CancelledError()
            if winner is not original:
                original.remove_listener('close',self.on_closed)
                original.remove_listener('websocket',self.watch_socket)
                self.page=winner
                winner.on('close',self.on_closed)
                winner.on('websocket',self.watch_socket)
            self.event('其中一個分頁已入場，保留成功分頁並清理其餘助手分頁')
        finally:
            for task in tasks:
                if not task.done():task.cancel()
            if tasks:await asyncio.gather(*tasks,return_exceptions=True)
            losers=[p for p in extras if p is not winner]
            if winner is not None and winner is not original:losers.append(original)
            for page in losers:
                try:await page.close()
                except Exception:self.event('部分助手分頁未能關閉，請手動確認')

    def begin_entry(self):
        if self.task and not self.task.done() and self.task is not asyncio.current_task():
            raise ValueError('此帳號已有背景任務，請先停止目前操作。')
        self.entry_pending=True
        self.entry_passed_at=None
        self.phase,self.note='recovering','等待入場；可在主視窗查看進度或停止。'
        self.cancel.clear();self.persist();self.event(self.note)
        self.task=asyncio.create_task(self.recover_entry())

    async def recover_entry(self):
        async with self.lock:
            if not self.entry_pending or self.phase not in {'idle','recovering'} or not self.page or self.page.is_closed():return
            try:
                text=await self.page.locator('body').inner_text()
                self.check_cloudflare(text)
                current=urlparse(self.page.url)
                if current.netloc!='on-line.1kuji.com':return
                if not entry_limited(text) and current.path not in {LIST_PATH,'/Form/Product/ProductDetail.aspx'}:
                    self.phase,self.note='idle','請在獨立視窗選擇商品；選定後自動監看。'
                    self.persist();return
                if entry_limited(text) and not self.config.get('entryRefresh', True):
                    self.phase, self.note = 'idle', '網站暫時限制入場；已關閉自動入場刷新，請手動操作。'
                    self.entry_pending = False
                    self.persist(); return
                self.phase='recovering';self.cancel.clear()
                if entry_limited(text):
                    await self.wait_entry_tabs()
                else:
                    await self.wait_temporary_page(entry_only=True)
                if self.cancel.is_set():return
                config=validate_config({**self.config,'url':self.page.url})
                if not config['pid']:
                    self.entry_passed_at=now()
                    self.phase,self.note='idle','已通過入場，請在獨立視窗選擇商品；選定後自動監看。'
                    self.persist();return
                self.config=config
                self.entry_passed_at=now()
                await self.follow_product_to_list()
                self.phase='idle'
                await self.start(self.config)
            except asyncio.CancelledError:raise
            except CloudflarePaused:return
            except Exception as error:
                self.phase,self.note='uncertain',f'入場接續未完成：{type(error).__name__}: {str(error)[:160]}'
                self.entry_pending=False;self.persist();self.event(self.note)

    async def follow_product_to_list(self):
        current = urlparse(self.page.url)
        if current.path != '/Form/Product/ProductDetail.aspx':
            return False
        if current.netloc != 'on-line.1kuji.com' or parse_qs(current.query).get('pid', [''])[0] != self.config['pid']:
            raise ValueError('商品介紹頁與設定商品不符，已停止。')
        button = self.page.get_by_role('link', name=re.compile(r'^\s*購入\s*(?:する)?\s*$')).or_(
            self.page.get_by_role('button', name=re.compile(r'^\s*購入\s*(?:する)?\s*$')))
        visible = [button.nth(i) for i in range(await button.count()) if await button.nth(i).is_visible()]
        if len(visible) != 1:
            raise ValueError('未找到唯一的購入入口，請確認登入或販售狀態。')
        self.event('從商品介紹頁進入選箱列表')
        await visible[0].click(timeout=8000, no_wait_after=True)
        await self.page.wait_for_url(lambda url: urlparse(str(url)).path == LIST_PATH, timeout=30000)
        await self.wait_temporary_page()
        _, pid = list_url(self.page.url)
        if pid != self.config['pid']:
            raise ValueError('購入入口導向其他商品，已停止。')
        self.config.update(url=self.page.url,pid=pid)
        await self.sync_cookies()
        return True

    async def fetch_boxes(self):
        started = time.monotonic()
        page = self.page
        if not page or page.is_closed():
            raise ValueError('Chrome 分頁已關閉，監看停止。')
        page_url = page.url
        _, pid = list_url(page_url)
        if pid != self.config['pid']:
            raise ValueError('目前分頁是其他商品，監看停止。')
        response = await page.evaluate(FETCH_BOX_HTML, page_url)
        if self.cancel.is_set():
            raise asyncio.CancelledError()
        if self.page is not page or page.url != page_url:
            raise ValueError('查詢期間分頁已切換，監看停止。')
        self.check_cloudflare(headers=response['headers'])
        if response['status'] != 200:
            raise ValueError('選箱查詢回傳 HTTP '+str(response['status'])+'，請查看網站。')
        _, pid = list_url(response['url'])
        if pid != self.config['pid']:
            raise ValueError('選箱查詢導向其他商品，監看停止。')
        body = response['html']
        self.check_cloudflare(BeautifulSoup(body, 'html.parser').get_text(' '))
        boxes = parse_boxes(body)
        self.metrics.update(lastCheckedAt=now(), requestMs=round((time.monotonic()-started)*1000))
        return boxes

    async def api_wait_count(self):
        if self.cloudflare_paused or not self.matches_target():
            return {}
        page, source = self.page, self.page.url
        try:
            response = await page.evaluate(FETCH_QUEUE_JSON, source)
            if self.page is not page or page.url != source or not self.matches_target():
                return {}
            self.check_cloudflare(headers=response['headers'])
            self.check_cloudflare(BeautifulSoup(response['text'], 'html.parser').get_text(' '))
            endpoint = ORIGIN + DETAIL_PATH + '/GetLotteryBoxWaitCount'
            if response['status'] != 200 or response['url'] != endpoint:
                raise ValueError('順位查詢回應不符')
            data = json.loads(response['text']).get('d')
            if isinstance(data, str):
                data = json.loads(data)
            value = data.get('your_waiting_no') if isinstance(data, dict) else None
            if isinstance(value, bool) or not re.fullmatch(r'\d+', str(value)):
                raise ValueError('順位查詢沒有有效個人順位')
            ahead = int(value)
            self.metrics['queueApiAt'] = now()
            if self.phase in {'submitting','waiting','uncertain'}:
                changed = self.queue_ahead != ahead or self.phase != 'waiting'
                self.queue_no = self.queue_ahead = ahead
                self.phase, self.note = 'waiting', '已確認個人順位；請保持視窗連線。'
                self.metrics.setdefault('confirmedAt', now())
                self.metrics['lastQueueAt'] = now()
                if changed:
                    self.event(f'前方還有 {ahead} 人')
                self.persist()
            return {'ahead':ahead}
        except CloudflarePaused:
            raise
        except (PlaywrightError, ValueError, TypeError, AttributeError):
            self.log_query_failure('順位')
            return {}

    def log_query_failure(self, kind):
        key = kind+'QueryErrorAt'
        if now() - self.metrics.get(key, 0) >= 60000:
            self.metrics[key] = now()
            self.event(kind+'查詢暫未取得有效資料，保留上次數值；請檢查登入、網站訊息或連線。')

    async def start(self, data):
        if self.phase not in {'idle','closed'}:
            raise ValueError('此帳號已有任務。先檢查網站狀態，再結束本次任務；不會覆蓋或重送。')
        # Require either a live HTTP session (cookie synced) or an open browser.
        # If the browser is open and on the same list page, also sync cookies first.
        has_session = bool(self.http_session and not self.http_session.closed)
        browser_open = bool(self.page and not self.page.is_closed())
        if self.cloudflare_paused:
            if not browser_open:
                raise CloudflarePaused(self.note)
            _, pid = list_url(self.page.url)
            body = await self.page.content()
            self.check_cloudflare(BeautifulSoup(body, 'html.parser').get_text(' '))
            parse_boxes(body)
            if pid != validate_config(data)['pid']:
                raise ValueError('請先回到設定商品的選箱列表。')
            self.cloudflare_paused = False
        if not has_session and not browser_open:
            raise ValueError('請先開啟獨立視窗並登入，以建立 HTTP session。')
        self.config = validate_config(data)
        if browser_open:
            gate = False
            if callable(getattr(self.page, 'content', None)):
                try:
                    res = self.page.content()
                    content = await res if asyncio.iscoroutine(res) else (res if isinstance(res, str) else '')
                    gate = entry_limited(BeautifulSoup(content, 'html.parser').get_text()) if content else False
                except Exception:
                    pass
            if (not self.config['pid'] or urlparse(self.config['url']).path != LIST_PATH
                    or urlparse(self.page.url).path == '/Form/Product/ProductDetail.aspx'
                    or gate):
                if gate and not self.config.get('entryRefresh', True):
                    raise ValueError('網站目前限制入場；已關閉自動入場刷新，請在獨立視窗手動操作。')
                self.begin_entry()
                return
        if not self.config['pid']:
            raise ValueError('請先開啟獨立視窗並選擇商品。')
        self.entry_pending=False
        # Sync cookies from browser when it is open so the HTTP session is fresh.
        if browser_open:
            if urlparse(self.page.url).path == '/Form/Product/ProductDetail.aspx':
                await self.wait_temporary_page()
                await self.follow_product_to_list()
            await self.sync_cookies()
            has_session = bool(self.http_session and not self.http_session.closed)
        if not has_session and not browser_open:
            raise ValueError('尚未登入或 Cookie 無效，請在獨立視窗重新登入。')
        # Establish baseline: use visible DOM if browser is open, otherwise HTTP fetch.
        if browser_open:
            boxes = parse_boxes(await self.page.content())
        else:
            boxes = await self.fetch_boxes()
        self.baseline = max((b['seq'] for b in boxes), default=0)
        self.phase, self.note = 'watching', f'基準 BOX-{self.baseline:05d}，等待新開滿箱。'
        self.target, self.queue_no = None, None
        self.queue_ahead, self.inventory = None, {}
        self.exit_available = self.refresh_available = False
        self.queue_alert = False
        self.queue_reason = None
        self.soldout_acknowledged = False
        self.metrics = {k:v for k,v in self.metrics.items() if k in {'lastCheckedAt','requestMs'}}
        self.metrics['startedAt'] = now()
        self.cancel = asyncio.Event()
        self.persist()
        self.event(f'開始監看新 {self.config["count"]} 枚箱；基準 {self.baseline:05d}')
        self.task = asyncio.create_task(self.hunt())

    async def navigate_list(self, data):
        if self.phase in {'watching','opening','submitting','leaving'} or not self.page or self.page.is_closed():
            raise ValueError('請先停止目前監看，或等候正在送出的操作完成。')
        url = urlparse(self.page.url)
        if url.path.startswith('/Form/Order/'):
            raise ValueError('目前在購買頁，請先在網站完成或取消。')
        signal = await self.read_detail()
        if signal.get('exitVisible') or signal.get('ahead') is not None:
            raise ValueError('目前仍在隊伍中，請使用「離開目前箱並監看」正式退出。')
        await self.cancel_observer()
        config = validate_config(data)
        await self.page.goto(config['url'], wait_until='domcontentloaded', timeout=30000)
        self.clear_queue_state()
        self.config = config
        self.phase, self.note = 'idle', '已開啟選箱列表，可以開始監看。'
        self.persist()

    async def cancel_observer(self):
        self.cancel.set()
        if self.task and self.task is not asyncio.current_task():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.task = None

    def clear_queue_state(self):
        self.target, self.queue_no, self.queue_ahead = None, None, None
        self.inventory, self.next_check = {}, None
        self.exit_available = self.refresh_available = False
        self.queue_alert, self.queue_reason = False, None
        self.soldout_attempt = None
        self.metrics.pop('queueApiAt', None)

    async def reconcile_queue_page(self, signal):
        current = signal.get('url')
        if not current:
            return False
        url = urlparse(current)
        if url.netloc != 'on-line.1kuji.com':
            self.phase, self.note = 'uncertain', '目前已離開商品頁，請重新查看或重啟此帳號。'
            self.queue_no = self.queue_ahead = None
            self.exit_available = False
            return False
        if url.path == LIST_PATH:
            if signal.get('exitVisible') or signal.get('ahead') is not None or (signal.get('number') or 0) > 0:
                return False
            # A returned list must never keep a stale personal rank or box lock.
            try:
                boxes = parse_boxes(await self.page.content())
            except ValueError:
                return False
            same_product = parse_qs(url.query).get('pid',[''])[0] == self.config.get('pid')
            config = dict(self.config)
            self.clear_queue_state()
            self.phase, self.note = 'idle', '網站已返回選箱列表，舊隊伍狀態已清除。'
            self.persist()
            self.event(self.note)
            if same_product:
                self.event('已確認返回同商品選箱列表，自動重新監看新滿箱')
                await self.start(config)
            return True
        if url.path == DETAIL_PATH:
            query = parse_qs(url.query)
            ident, pid = query.get('lbdid',[''])[0], query.get('pid',[''])[0]
            if re.fullmatch(r'[0-9A-Fa-f]{16}', ident) and re.fullmatch(r'[A-Za-z0-9_]{1,80}',pid):
                if ident != (self.target or {}).get('id'):
                    self.target = {'id':ident.upper(),'seq':None}
                    self.inventory = {}
                    self.metrics.pop('queueApiAt', None)
                    self.queue_no = self.queue_ahead = None
                    self.metrics.pop('readyAt',None)
                    self.queue_alert = False
                    self.queue_reason = None
                    self.config.update(url=ORIGIN+LIST_PATH+'?'+urlencode({'pid':pid,'pno':1}),pid=pid)
                    if signal.get('ahead') is not None or signal.get('ready') or signal.get('exitVisible'):
                        self.phase = 'waiting' if signal.get('ahead') is not None else ('ready' if signal.get('ready') else 'waiting')
                        self.queue_no = self.queue_ahead = signal.get('ahead')
                        self.note = f'已同步視窗箱號，前方還有 {self.queue_ahead} 人。' if self.queue_ahead is not None else '已同步視窗箱號與隊伍狀態。'
                    else:
                        self.phase, self.note = 'uncertain', '已依目前視窗更新箱號，重新讀取隊伍狀態。'
                    self.persist()
                    self.event('目前視窗箱號已變更，舊箱號鎖定已解除')
                else:
                    if signal.get('ahead') is not None or signal.get('ready') or signal.get('exitVisible'):
                        if self.phase in {'uncertain', 'idle'} or not self.task or self.task.done():
                            if signal.get('ready'):
                                self.phase = 'ready'
                                self.signal_ready()
                            elif signal.get('ahead') is not None:
                                self.queue_no = self.queue_ahead = signal['ahead']
                                self.phase, self.note = 'waiting', f'已接續隊伍，前方還有 {self.queue_ahead} 人。'
                            else:
                                self.phase, self.note = 'waiting', '已同步隊伍狀態。'
                            self.cancel = asyncio.Event()
                            self.task = asyncio.create_task(self.observe_queue())
                            self.persist()
                            self.event('已接續目前箱號之排隊狀態')
        return False

    async def inspect_current(self):
        if not self.page or self.page.is_closed():
            raise ValueError('請先開啟獨立視窗。')
        if self.phase in {'opening','submitting','leaving'}:
            raise ValueError('目前操作正在送出，請稍後重新查看。')
        if self.phase == 'watching':
            return
        await self.cancel_observer()
        signal = await self.read_detail()
        self.cloudflare_paused = False
        if await self.reconcile_queue_page(signal):
            return
        if signal.get('exitVisible') or signal.get('ahead') is not None or signal.get('ready'):
            self.cancel = asyncio.Event()
            self.task = asyncio.create_task(self.observe_queue())
            if signal.get('ready'):
                self.phase = 'ready'
                self.signal_ready()
            elif signal.get('ahead') is not None:
                self.queue_ahead = self.queue_no = signal['ahead']
                self.phase, self.note = 'waiting', f'已接續隊伍，前方還有 {self.queue_ahead} 人。'
            else:
                self.phase, self.note = 'waiting', '已重新接續目前視窗的隊伍資訊。'
        else:
            inventory = self.inventory
            self.clear_queue_state()
            self.inventory = inventory
            self.phase, self.note = 'idle', '目前頁面未顯示個人隊伍，可返回選箱列表。'
        self.persist()

    async def restart_account(self, data):
        await self.cancel_observer()
        await self.open({**data, 'chooseProfile':True})
        self.event('已選擇並綁定 Chrome 設定檔，請確認帳號與商品。')

    async def hunt(self):
        try:
            empty_since = None
            first_check = True
            network_failures = 0
            while not self.cancel.is_set():
                delay = 0 if first_check else random.uniform(self.config['minSeconds'], self.config['maxSeconds'])
                first_check = False
                self.next_check = now() + round(delay*1000)
                if delay:
                    try:
                        await asyncio.wait_for(self.cancel.wait(), timeout=delay)
                        return
                    except TimeoutError:
                        pass
                if self.cancel.is_set():
                    return
                if urlparse(self.page.url).path != LIST_PATH:
                    raise ValueError('獨立視窗已離開選箱列表，已停止監看。')
                try:
                    boxes = await self.fetch_boxes()
                except (TimeoutError, aiohttp.ClientConnectionError) as error:
                    network_failures += 1
                    reason = type(error).__name__ + (': ' + str(error)[:160] if str(error) else '')
                    if network_failures >= 3:
                        raise ValueError(f'連續3次查詢連線失敗，監看停止：{reason}') from error
                    self.note = f'查詢暫時失敗（{network_failures}/3）：{reason}；等待後重試。'
                    self.event(self.note)
                    self.persist()
                    try:
                        await asyncio.wait_for(self.cancel.wait(), timeout=5 * network_failures)
                        return
                    except TimeoutError:
                        pass
                    continue
                if network_failures:
                    self.event('查詢連線恢復，繼續監看新箱')
                    self.note = '查詢連線已恢復，繼續等待新開滿箱。'
                    network_failures = 0
                if self.cancel.is_set():
                    return
                if not boxes:
                    if empty_since is None:
                        empty_since = time.monotonic()
                        self.note = '列表目前沒有籤筒，等待新箱；連續1小時無箱將停止監看。'
                        self.event(self.note)
                    if time.monotonic() - empty_since >= 3600:
                        self.phase, self.note = 'idle', '列表連續1小時無籤筒，已停止監看。'
                        self.persist();self.event(self.note)
                        return
                    continue
                if empty_since is not None:
                    self.event('列表出現籤筒，無箱等待計時已歸零')
                    empty_since = None
                candidate = select_box(boxes, self.baseline, self.config['count'])
                if candidate:
                    self.target = candidate
                    self.metrics['foundAt'] = now()
                    self.phase, self.note = 'opening', f'發現新箱 BOX-{candidate["seq"]:05d}，準備排隊。'
                    self.next_check = None
                    self.persist()
                    self.event(self.note)
                    await self.enter_queue()
                    return
        except asyncio.CancelledError:
            raise
        except CloudflarePaused:
            return
        except Exception as e:
            self.phase, self.note = 'uncertain', (type(e).__name__ + ': ' + (str(e) or '未提供詳細訊息'))[:300]
            self.persist()
            self.event(self.note)
        finally:
            self.next_check = None

    async def enter_queue(self):
        stage = time.monotonic()
        self.event('開始載入新箱頁面')
        await self.page.goto(detail_url(self.config['pid'], self.target), wait_until='domcontentloaded', timeout=30000)
        await self.wait_temporary_page()
        self.metrics['detailLoadedAt'] = now()
        self.event(f'箱頁載入完成，耗時 {round((time.monotonic()-stage)*1000)} ms')
        if self.cancel.is_set():
            return
        button = self.page.locator('a.waitingStart[id$="_lbAddQueue"], a[id$="_lbAddToCart"]:visible')
        await button.wait_for(state='visible', timeout=8000)
        if await button.count() != 1 or not await button.is_visible():
            raise ValueError('未找到排隊按鈕，請檢查網站訊息。')
        button_id = await button.get_attribute('id') or ''
        if button_id.endswith('_lbAddToCart'):
            current = urlparse(self.page.url)
            query = parse_qs(current.query)
            if (current.netloc != 'on-line.1kuji.com' or current.path != DETAIL_PATH
                    or query.get('pid', [''])[0] != self.config['pid']
                    or query.get('lbdid', [''])[0].upper() != self.target['id'].upper()
                    or re.sub(r'\s+', '', await button.inner_text()) != 'このくじ箱にする'):
                raise ValueError('選箱入口與鎖定箱子不符，已停止。')
        elif await button.get_attribute('data-product-id') != self.config['pid'] or await button.get_attribute('data-display-id') != self.target['id']:
            raise ValueError('排隊按鈕與鎖定箱子不符，已停止。')
        self.metrics['buttonReadyAt'] = now()
        self.event(f'排隊按鈕可用，商品與箱號核對成功，距進箱 {round((time.monotonic()-stage)*1000)} ms')
        self.phase, self.note = 'submitting', '已記錄一次提交，等待網站個人順位；不重送。'
        self.metrics['submittedAt'] = now()
        self.persist()  # Durable before the single click, including across process crashes.
        self.event('即將點擊排隊按鈕（單次提交）')
        await button.click(timeout=8000, no_wait_after=True)
        elapsed = now() - self.metrics.get('foundAt', self.metrics['submittedAt'])
        self.event(f'已觸發網站排隊按鈕一次；發現新箱至點擊完成 {elapsed} ms')
        # Sync cookies immediately after the click so the HTTP session has the
        # latest session state for API-only queue tracking.
        try:
            await asyncio.sleep(1)  # brief wait for page to settle after click
            await self.sync_cookies()
        except Exception:
            pass
        await self.observe_queue()

    async def _api_poll_loop(self):
        """Read queue JSON every 10 s and inventory HTML every 180 s through the logged-in page."""
        POLL_INTERVAL = 10.0
        last_inv_api = 0.0
        while not self.cancel.is_set():
            if self.phase in {'submitting', 'waiting', 'ready'}:
                # 1. Poll API wait count
                try:
                    await self.api_wait_count()
                except CloudflarePaused:
                    return
                if self.cancel.is_set():
                    return

                # 2. Automatically refresh inventory via API every 3 minutes (180s)
                # or immediately if not yet queried from API
                now_mono = time.monotonic()
                if last_inv_api == 0 or now_mono - last_inv_api >= 180:
                    last_inv_api = now_mono
                    try:
                        await self.query_inventory_api()
                    except CloudflarePaused:
                        return
                    except Exception:
                        self.log_query_failure('庫存')

            try:
                await asyncio.wait_for(self.cancel.wait(), timeout=POLL_INTERVAL)
                return
            except TimeoutError:
                pass

    async def observe_queue(self):
        """Combine visible queue signals with same-profile requests; keep the browser page open."""
        pending_since = time.monotonic()
        navigation_errors = 0
        # Launch the API polling companion task.
        poll_task = asyncio.create_task(self._api_poll_loop())
        try:
            while not self.cancel.is_set():
                page_alive = self.page and not self.page.is_closed()
                api_alive = bool(self.http_session and not self.http_session.closed)
                if not page_alive and not api_alive:
                    break
                # DOM path: only while the browser page is open.
                if page_alive:
                    try:
                        signal = await self.read_detail()
                        navigation_errors = 0
                    except CloudflarePaused:
                        return
                    except Exception:
                        navigation_errors += 1
                        if not self.page or self.page.is_closed() or navigation_errors > 30:
                            # Browser gone; switch to API-only mode.
                            if api_alive:
                                self.note = '獨立視窗關閉，改由背景連線持續更新順位。'
                                self.persist()
                                break
                            raise
                        await asyncio.sleep(0.5)
                        continue
                    if await self.reconcile_queue_page(signal):
                        return
                    if signal.get('paymentTimeout'):
                        if not self.soldout_task or self.soldout_task.done():
                            self.queue_reason = 'PaymentTimeout'
                            self.phase, self.note = 'uncertain', '付款逾時已取消，正在確認後重新排隊。'
                            self.persist()
                            self.soldout_task = asyncio.create_task(self.resume_after_payment_timeout())
                        return
                    if signal.get('soldOut'):
                        self.queue_reason = 'SoldOut'
                        self.queue_alert = True
                        self.phase, self.note = 'uncertain', '箱子售完，正在等待網站返回選箱列表。'
                        self.persist()
                        if not self.soldout_acknowledged:
                            self.soldout_acknowledged = True
                            self.event('網站顯示售完，確認返回選箱列表')
                            try:
                                await self.page.locator('#customAlert .ok-button').click(timeout=5000, no_wait_after=True)
                            except Exception:
                                pass
                    if self.queue_alert:
                        await asyncio.sleep(1)
                        continue
                    if signal['ready']:
                        self.signal_ready()
                    elif (signal.get('ahead') is not None or (signal.get('number') is not None and signal['number'] > 0)) and self.phase != 'ready':
                        number = signal['ahead'] if signal.get('ahead') is not None else signal['number']
                        if self.queue_ahead is None or number < self.queue_ahead:
                            self.queue_no = number
                            self.queue_ahead = number
                            self.phase, self.note = 'waiting', '已確認個人順位；請保持獨立視窗開啟。'
                            self.metrics.setdefault('confirmedAt', now())
                            self.metrics['lastQueueAt'] = now()
                            self.persist()
                            self.event(f'前方還有 {self.queue_ahead} 人')
                    elif self.phase == 'submitting' and time.monotonic()-pending_since > 30:
                        self.phase, self.note = 'uncertain', '30 秒內未確認順位，請人工檢查；不會重送。'
                        self.persist()
                        self.event(self.note)
                try:
                    await asyncio.wait_for(self.cancel.wait(), timeout=1)
                except TimeoutError:
                    pass
            # API-only phase: keep alive until cancel or terminal signal arrives.
            if api_alive and not self.cancel.is_set():
                while not self.cancel.is_set():
                    if self.phase in {'ready', 'uncertain'}:
                        break
                    try:
                        await asyncio.wait_for(self.cancel.wait(), timeout=5)
                    except TimeoutError:
                        pass
        except Exception as e:
            if not self.cancel.is_set():
                self.phase, self.note = 'uncertain', f'無法讀取排隊頁面：{str(e)[:180]}'
                self.persist()
        finally:
            poll_task.cancel()
            try:
                await poll_task
            except asyncio.CancelledError:
                pass

    async def read_detail(self):
        signal = await self.page.evaluate(READ_DETAIL)
        self.check_cloudflare(signal.get('text', ''))
        info = parse_detail_text(signal.get('text', ''))
        self.exit_available = bool(signal.get('exitVisible'))
        self.refresh_available = bool(signal.get('refreshEnabled'))
        if (info['remaining'] is not None or info['prizes']):
            if not self.inventory or self.inventory.get('source') != 'api':
                self.inventory = {k:v for k,v in info.items() if k != 'ahead'}
                self.inventory['readAt'] = now()
        signal['ahead'] = (self.queue_ahead if now()-self.metrics.get('queueApiAt', 0) < 30000
                           else info['ahead'])
        return signal

    def log_inventory_response(self, html, status, path):
        # Log only response categories; never HTML, cookies, user IDs or URL queries.
        soup = BeautifulSoup(html or '', 'html.parser')
        text = soup.get_text(' ', strip=True)
        login = bool(soup.select('input[type="password"]')) or 'Login' in (path or '')
        limited = ('一時的' in text or 'アクセスを制限' in text) and '残りくじ' not in text
        kind = '登入頁' if login else '疑似暫時限制頁' if limited else '缺少可辨識庫存欄位'
        self.event(f'籤數回應診斷：HTTP {status}；{kind}；包含剩餘籤數文字={"是" if "残りくじ" in text else "否"}')

    async def query_inventory_api(self):
        if self.cloudflare_paused or self.phase in {'watching','opening','leaving'}:
            return {}
        if not self.page or self.page.is_closed():
            return {}
        current = urlparse(self.page.url)
        if current.netloc != 'on-line.1kuji.com' or current.path != DETAIL_PATH:
            return {}
        source, page = self.page.url, self.page
        response = await page.evaluate(FETCH_BOX_HTML, source)
        if self.page is not page or page.url != source:
            return {}
        self.check_cloudflare(headers=response['headers'])
        self.check_cloudflare(BeautifulSoup(response['html'], 'html.parser').get_text(' '))
        returned = urlparse(response['url'])
        expected = parse_qs(current.query)
        actual = parse_qs(returned.query)
        if (response['status'] != 200 or returned.netloc != current.netloc or returned.path != DETAIL_PATH
                or any(actual.get(key) != expected.get(key) for key in ('pid','lbdid'))):
            self.log_query_failure('庫存')
            return {}
        info = parse_detail_html(response['html'])
        if info['remaining'] is None and not info['prizes']:
            self.log_query_failure('庫存')
            return {}
        self.inventory = {k:v for k,v in info.items() if k != 'ahead'}
        self.inventory.update(source='api', readAt=now())
        if self.phase in {'submitting','waiting','ready','uncertain'}:
            await self.api_wait_count()
        if self.page is not page or page.url != source:
            return {}
        self.persist()
        self.event(f'已查詢最新籤數：剩餘 {info["remaining"]} 枚')
        if info['remaining'] == 0 and self.target and self.matches_target():
            key = (self.config.get('pid'), self.target['id'])
            self.queue_reason, self.queue_alert = 'SoldOut', True
            if (self.config.get('autoResumeSoldOut', True) and self.soldout_attempt != key
                    and (not self.soldout_task or self.soldout_task.done())):
                self.soldout_attempt = key
                self.soldout_task = asyncio.create_task(self.resume_after_soldout(key))
        return self.inventory

    async def resume_after_soldout(self,key):
        async with self.lock:
            if (self.manager.shutting_down or key!=(self.config.get('pid'),(self.target or {}).get('id'))
                    or self.queue_reason!='SoldOut' or not self.config.get('autoResumeSoldOut',True)):
                return
            if not self.page or self.page.is_closed():
                self.event('籤筒已售完，請開啟獨立視窗後離箱重新監看。')
                return
            self.event('查詢確認0籤，自動離開本箱並返回列表監看')
            try:
                await self.leave_and_requeue()
            except Exception as error:
                self.event('售完後重新監看未完成：'+str(error)[:200])

    async def resume_after_payment_timeout(self):
        async with self.lock:
            try:
                if self.manager.shutting_down or self.queue_reason != 'PaymentTimeout':
                    return
                signal = await self.read_detail()
                if not signal.get('paymentTimeout'):
                    return
                target = dict(self.target or {})
                pid = self.config.get('pid')
                current = urlparse(self.page.url)
                if current.netloc != 'on-line.1kuji.com' or parse_qs(current.query).get('pid',[''])[0] != pid or not target.get('id'):
                    raise ValueError('商品或箱號不符，停止自動重排。')
                self.event('確認付款逾時取消，單次確認後重新排隊')
                await self.page.locator('#customAlert .ok-button').click(timeout=5000, no_wait_after=True)
                await self.page.wait_for_url(lambda value: urlparse(str(value)).path == LIST_PATH
                    and parse_qs(urlparse(str(value)).query).get('pid',[''])[0] == pid, timeout=15000)
                signal = await self.read_detail()
                if signal.get('exitVisible') or signal.get('ahead') is not None or signal.get('ready'):
                    raise ValueError('仍有有效隊伍，停止自動重排。')
                boxes = parse_boxes(await self.page.content())
                candidate = next((box for box in boxes if box['id'] == target['id'] and box['amount'] > 0), None)
                if candidate is None:
                    raise ValueError('原箱已無庫存或不存在，請重新選箱。')
                await self.cancel_observer()
                self.cancel = asyncio.Event()
                self.clear_queue_state()
                self.target = candidate
                self.phase, self.note = 'opening', '逾時取消已確認，重新排入原箱。'
                self.persist()
                await self.enter_queue()
            except Exception as error:
                self.phase, self.note = 'uncertain', '逾時重排未完成：'+str(error)[:200]
                self.persist()
                self.event(self.note)

    async def _auto_heal_uncertain(self):
        try:
            await self.inspect_current()
        except Exception:
            pass
        finally:
            self._healing = False

    async def refresh_inventory(self):
        if self.phase in {'opening','submitting','leaving'} or not self.page or self.page.is_closed():
            raise ValueError('請先進入箱子，並等目前操作完成。')
        current = urlparse(self.page.url)
        if current.netloc != 'on-line.1kuji.com' or current.path != DETAIL_PATH:
            raise ValueError('目前不是箱子詳情頁，可先按「重新查看／修復」。')
        # Normal browser reload is the F5 operation. Never click the site's
        # inventory refresh button, and do not impose its button cooldown.
        await self.page.reload(wait_until='domcontentloaded', timeout=15000)
        signal = await self.read_detail()
        if signal.get('ahead') is not None or signal.get('ready') or signal.get('exitVisible'):
            if self.phase in {'uncertain', 'idle'} or not self.task or self.task.done():
                self.cancel = asyncio.Event()
                self.task = asyncio.create_task(self.observe_queue())
                self.note = '已接續目前視窗的隊伍資訊。'
                self.persist()
        self.event('已執行整頁重新整理（F5），未點網站庫存更新按鈕')

    def matches_target(self):
        if not self.page or not self.target:
            return False
        url = urlparse(self.page.url)
        query = parse_qs(url.query)
        return (url.scheme == 'https' and url.netloc == 'on-line.1kuji.com'
                and url.path == DETAIL_PATH and query.get('pid',[''])[0] == self.config.get('pid')
                and query.get('lbdid',[''])[0] == self.target.get('id'))

    async def wait_turn_then_requeue(self, config, box_id):
        acknowledged = False
        try:
            while not self.cancel.is_set():
                signal = await self.read_detail()
                current = urlparse(signal['url'])
                query = parse_qs(current.query)
                if current.netloc != 'on-line.1kuji.com' or query.get('pid',[''])[0] != config['pid']:
                    raise ValueError('已離開原商品，停止等待離箱。')
                if current.path == LIST_PATH:
                    async with self.lock:
                        self.phase = 'idle'
                        await self.leave_and_requeue()
                    return
                if current.path != DETAIL_PATH or query.get('lbdid',[''])[0] != box_id:
                    raise ValueError('目前頁面或箱號已變更，停止等待離箱。')
                if signal.get('exitVisible'):
                    async with self.lock:
                        self.phase = 'idle'
                        await self.leave_and_requeue()
                    return
                if signal.get('paymentTimeout') and not acknowledged:
                    acknowledged = True
                    self.event('已要求離箱，確認網站明示的逾時取消後等待返回列表')
                    await self.page.locator('#customAlert .ok-button').click(timeout=5000, no_wait_after=True)
                await asyncio.sleep(1)
        except CloudflarePaused:
            return
        except Exception as error:
            self.phase, self.note = 'uncertain', '等待離箱未完成：'+str(error)[:200]
            self.persist()
            self.event(self.note)

    async def leave_and_requeue(self):
        if self.phase in {'watching','opening','submitting','leaving'} or not self.page or self.page.is_closed():
            raise ValueError('請先停止監看，或等候正在送出的操作完成。')
        current = urlparse(self.page.url)
        if current.scheme != 'https' or current.netloc != 'on-line.1kuji.com' or current.path not in {LIST_PATH,DETAIL_PATH}:
            raise ValueError('請在目前視窗開啟選箱或箱子詳情頁；也可重啟此帳號視窗。')
        pid = parse_qs(current.query).get('pid',[''])[0]
        data = dict(self.config)
        data['url'] = ORIGIN+LIST_PATH+'?'+urlencode({'pid':pid,'pno':1})
        config = validate_config(data)
        # Explicit recovery follows the actual page, not a stale recorded box ID.
        exit_button = self.page.locator('[id$="_lbExitQueue"]')
        has_exit = await exit_button.count() == 1 and await exit_button.is_visible()
        signal = await self.read_detail()
        if current.path == DETAIL_PATH and not has_exit and signal.get('ready'):
            await self.cancel_observer()
            self.cancel = asyncio.Event()
            self.config = config
            self.phase, self.note = 'recovering', '已要求離箱；目前輪到你且網站沒有退出入口，等待網站釋放名額並返回列表後重新監看，可按停止取消。'
            self.persist()
            self.event(self.note)
            box_id = parse_qs(current.query).get('lbdid',[''])[0]
            self.task = asyncio.create_task(self.wait_turn_then_requeue(config, box_id))
            return
        if not has_exit and signal.get('ahead') is not None:
            raise ValueError('網站仍顯示隊伍但退出入口尚未出現，請重新查看或重啟此帳號。')
        await self.cancel_observer()
        self.cancel = asyncio.Event()
        self.phase, self.note = 'leaving', '依目前視窗退出／返回列表，確認成功後重新監看。'
        self.exit_available = self.refresh_available = False
        self.persist()
        try:
            if has_exit:
                await exit_button.click(timeout=8000, no_wait_after=True)
                dialog = self.page.locator('#customConfirm')
                await dialog.wait_for(state='visible', timeout=8000)
                text = await dialog.inner_text()
                if 'くじ箱選択へ戻りますか' not in text or '順番待ち' not in text:
                    raise ValueError('網站確認視窗內容不符，未自動同意。')
                await dialog.get_by_role('button', name='はい', exact=True).click(timeout=8000, no_wait_after=True)
                await self.page.wait_for_url(lambda url: urlparse(str(url)).netloc == 'on-line.1kuji.com'
                    and urlparse(str(url)).path == LIST_PATH
                    and parse_qs(urlparse(str(url)).query).get('pid',[''])[0] == config['pid'], timeout=15000)
            elif current.path == DETAIL_PATH:
                await self.page.goto(config['url'],wait_until='domcontentloaded',timeout=15000)
            await self.page.wait_for_load_state('domcontentloaded', timeout=15000)
            await self.wait_temporary_page()
            await self.follow_product_to_list()
            returned = urlparse(self.page.url)
            if returned.netloc != 'on-line.1kuji.com' or returned.path != LIST_PATH or parse_qs(returned.query).get('pid',[''])[0] != config['pid']:
                raise ValueError('網站尚未返回同商品選箱列表，未啟動監看。')
            parse_boxes(await self.page.content())
            text = await self.page.locator('body').inner_text()
            if parse_detail_text(text)['ahead'] is not None:
                raise ValueError('頁面仍顯示個人隊伍，未重新啟動。')
            exit_button = self.page.locator('[id$="_lbExitQueue"]')
            if await exit_button.count() and await exit_button.is_visible():
                raise ValueError('頁面仍有退出排隊按鈕，未重新啟動。')
            self.event('已確認離開本箱並返回選箱列表')
            self.clear_queue_state()
            self.phase, self.note = 'idle', '已確認回到列表，重新建立監看基準。'
            self.persist()
            self.event('已確認離開目前箱／舊隊伍，重新監看')
            await self.start(config)
            self.metrics['requeuedAt'] = now()
            self.persist()
        except Exception as e:
            self.phase, self.note = 'uncertain', f'退出／重排未完成：{str(e)[:220]}；可重新查看或重啟此帳號。'
            self.persist()
            self.event(self.note)
            raise ValueError(self.note) from e

    async def stop(self):
        if self.phase not in {'watching','recovering'} and not self.entry_pending:
            raise ValueError('只有監看中的任務可停止；不會代你退出既有隊伍。')
        self.entry_pending=False
        self.cancel.set()
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        self.phase, self.note, self.next_check = 'idle', '已停止監看。', None
        self.persist()
        self.event(self.note)

    async def reset(self):
        if self.phase not in {'uncertain','waiting','ready'}:
            raise ValueError('目前不能結束任務，請先停止監看或等候排隊結果。')
        self.cancel.set()
        if self.task:
            await self.task
        self.phase, self.note = ('idle' if self.page and not self.page.is_closed() else 'closed'), '已結束助手任務；網站隊伍不會因此取消。'
        self.target, self.queue_no, self.next_check = None, None, None
        self.queue_ahead, self.inventory = None, {}
        self.exit_available = self.refresh_available = False
        self.persist()
        self.event(self.note)


class Manager:
    def __init__(self, runtime, login_only=False):
        self.login_only = login_only
        self.runtime = Path(runtime)
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.token = secrets.token_urlsafe(32)
        self.playwright = None
        self.attached_browser = None
        self.profile_directories = {}
        self.browser_lock = asyncio.Lock()
        self.picker_lock = asyncio.Lock()
        self.exit_requested = asyncio.Event()
        self.shutting_down = False
        self.accounts = {i:Account(self, i) for i in 'ABC'}

    def browser_disconnected(self, browser):
        if self.attached_browser is not browser:
            return
        self.attached_browser = None
        self.profile_directories.clear()
        for account in self.accounts.values():
            if account.context is None and account.page is None:
                continue
            account.cancel.set()
            for task in (account.task, account.soldout_task):
                if task and not task.done():
                    task.cancel()
            account.entry_pending = False
            account.context = account.page = None
            account.phase = 'uncertain' if account.target else 'closed'
            account.note = 'Chrome 連線已中斷，請按連接 Chrome 後重新確認網站狀態。'
            account.event(account.note)
            account.persist()

    async def shutdown(self):
        # Finish queues before shutdown: stopping the browser driver can close
        # managed windows or interrupt the website's queue connection.
        for a in self.accounts.values():
            a.cancel.set()
        pending = [a.soldout_task for a in self.accounts.values() if a.soldout_task and not a.soldout_task.done()]
        for task in pending:task.cancel()
        if pending:await asyncio.gather(*pending,return_exceptions=True)
        tasks = [a.task for a in self.accounts.values() if a.task]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        # Close all aiohttp sessions cleanly.
        for a in self.accounts.values():
            if a.http_session and not a.http_session.closed:
                await a.http_session.close()
        if self.playwright:
            await self.playwright.stop()


def create_app(manager):
    @web.middleware
    async def security(request, handler):
        if request.host not in {'127.0.0.1:18766', 'localhost:18766'}:
            raise web.HTTPForbidden(text='Invalid host')
        origin = request.headers.get('Origin')
        if origin and origin not in {'http://127.0.0.1:18766','http://localhost:18766'}:
            raise web.HTTPForbidden(text='Invalid origin')
        if request.path.startswith('/api/') and not secrets.compare_digest(request.headers.get('Authorization',''), 'Bearer '+manager.token):
            raise web.HTTPUnauthorized(text='Invalid session')
        try:
            response = await handler(request)
        except web.HTTPException:
            raise
        except (ValueError, KeyError, TypeError) as e:
            response = web.json_response({'error':str(e)}, status=400)
        except Exception as e:
            response = web.json_response({'error':str(e)[:300]}, status=500)
        response.headers.update({'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'", 'Referrer-Policy':'no-referrer'})
        return response
    app = web.Application(middlewares=[security], client_max_size=8192)

    async def state(request):
        try:
            discord = json.loads((manager.runtime/'discord-status.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            discord = {'enabled':False}
        return web.json_response({'version':VERSION, 'loginOnly':manager.login_only, 'accounts':[a.state() for a in manager.accounts.values()], 'notifications':discord})

    async def action(request):
        if manager.shutting_down:
            raise ValueError('服務正在重新啟動，請稍候。')
        data = await request.json()
        ident, command = data.get('id'), data.get('action')
        if manager.login_only and command not in {'open','focus','label','config','restart'}:
            raise ValueError('背景服務已關閉，目前僅能手動登入。')
        if ident not in manager.accounts:
            raise ValueError('帳號無效。')
        a = manager.accounts[ident]
        # Entry recovery holds the account lock while waiting on the website.
        if command == 'open' and a.page and not a.page.is_closed() and a.phase == 'recovering':
            try:
                await asyncio.wait_for(a.focus_window(), timeout=8)
            except TimeoutError:
                raise ValueError('Chrome 切回視窗未回應；入場任務仍在執行，請查看該帳號視窗。') from None
            return web.json_response({'ok':True,'account':a.state()})
        if command=='stop' and a.phase=='recovering':
            await a.stop()
            return web.json_response({'ok':True,'account':a.state()})
        if command=='restart' and data.get('confirmed') is True and (a.phase=='recovering' or a.entry_pending):
            await a.stop()
        async with a.lock:
            if command == 'open':
                async with manager.browser_lock:
                    if manager.playwright is None:
                        manager.playwright = await async_playwright().start()
                await a.open(data)
            elif command == 'start':
                await a.start(data)
            elif command == 'navigate':
                await a.navigate_list(data)
            elif command == 'stop':
                await a.stop()
            elif command == 'requeue':
                if data.get('confirmed') is not True:
                    raise ValueError('請確認放棄目前隊伍並重新監看。')
                await a.leave_and_requeue()
            elif command == 'inspect':
                await a.inspect_current()
            elif command == 'restart':
                if data.get('confirmed') is not True:
                    raise ValueError('請確認重啟此帳號視窗可能中斷目前隊伍。')
                async with manager.browser_lock:
                    if manager.playwright is None:
                        manager.playwright = await async_playwright().start()
                await a.restart_account(data)
            elif command == 'api_inventory':
                await a.query_inventory_api()
            elif command == 'inventory':
                try:
                    await a.query_inventory_api()
                except Exception:
                    await a.refresh_inventory()
            elif command == 'reset':
                if data.get('confirmed') is not True:
                    raise ValueError('請確認已檢查網站狀態。')
                await a.reset()
            elif command == 'focus':
                await a.focus_window()
            elif command == 'label':
                a.label = str(data.get('label','')).strip()[:24] or f'帳號 {ident}'
                a.persist()
            elif command == 'config':
                a.config.update(validate_config(data))
                a.persist()
            else:
                raise ValueError('未知操作。')
        return web.json_response({'ok':True, 'account':a.state()})

    async def control(request):
        data = await request.json()
        if data.get('action') == 'resume' and not manager.shutting_down:
            if manager.login_only:
                spawn_notifier(manager.runtime)
                manager.login_only = False
            return web.json_response({'ok':True})
        if data.get('action') != 'shutdown' or data.get('confirmed') is not True:
            raise ValueError('請確認停止服務可能中斷獨立視窗與隊伍。')
        manager.shutting_down = True
        asyncio.get_running_loop().call_later(0.3, manager.exit_requested.set)
        return web.json_response({'ok':True})

    async def static(request):
        name = request.match_info.get('name') or 'index.html'
        if name not in {'index.html','app.js','style.css'}:
            raise web.HTTPNotFound()
        return web.FileResponse(HERE / 'web' / name)
    app.router.add_get('/api/state', state)
    app.router.add_post('/api/action', action)
    app.router.add_post('/api/control', control)
    app.router.add_get('/', static)
    app.router.add_get('/{name}', static)
    async def cleanup(app):
        await manager.shutdown()
    app.on_cleanup.append(cleanup)
    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--login-only', action='store_true')
    args = parser.parse_args()
    args.runtime.mkdir(parents=True, exist_ok=True)
    session_file = args.runtime / 'panel-session.json'
    if session_file.exists():
        try:
            existing = json.loads(session_file.read_text(encoding='utf-8'))
            request = Request('http://127.0.0.1:18766/api/state', headers={'Authorization':'Bearer '+existing['token']})
            with urlopen(request, timeout=2) as response:
                if response.status == 200:
                    existing_url = 'http://127.0.0.1:18766/#' + existing['token']
                    print('Kuji Manager: http://127.0.0.1:18766/', flush=True)
                    if not args.no_browser:
                        webbrowser.open(existing_url)
                    return
        except Exception:
            pass
    listener=bind_listener()
    if listener is None:
        print('另一份背景服務已在執行，未重複啟動或修改登入憑證。',flush=True)
        return
    if not args.login_only:
        spawn_notifier(args.runtime)
    manager = Manager(args.runtime, login_only=args.login_only)
    url = 'http://127.0.0.1:18766/#' + manager.token
    async def open_panel(app):
        remember_runtime(args.runtime)
        session_file.write_text(json.dumps({'token':manager.token}), encoding='utf-8')
        (args.runtime / 'manager.pid').write_text(str(os.getpid()), encoding='utf-8')
        print('Kuji Manager: http://127.0.0.1:18766/', flush=True)
        if not args.no_browser:
            asyncio.get_running_loop().call_later(1, webbrowser.open, url)
    app = create_app(manager)
    app.on_startup.append(open_panel)
    async def serve():
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        try:
            await web.SockSite(runner, sock=listener).start()
            await manager.exit_requested.wait()
        finally:
            await runner.cleanup()
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass
    finally:
        listener.close()


if __name__ == '__main__':
    main()
