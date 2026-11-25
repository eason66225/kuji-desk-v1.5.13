"""Discord notifications from the local API; never touches the queue browser."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from service_runtime import background_environment
import sys
import time
from urllib.parse import urlparse

import aiohttp


def save_json(path, value):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)


def validate_webhook(value):
    value = str(value).strip()
    url = urlparse(value)
    if (url.scheme != 'https' or url.netloc != 'discord.com' or url.query or url.fragment
            or not re.fullmatch(r'/api(?:/v\d+)?/webhooks/\d+/[A-Za-z0-9_.-]+', url.path)):
        raise ValueError('Discord Webhook 格式無效。')
    return value


def event_key(account):
    metrics = account.get('metrics') or {}
    parts = [account.get('id'), (account.get('target') or {}).get('id'),
             metrics.get('startedAt') or metrics.get('foundAt') or 'unstarted', account.get('phase')]
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()


def payload_for(account, event_type=None):
    ready = account.get('phase') == 'ready'
    waiting = account.get('phase') == 'waiting'
    sold_out = (event_type == 'sold_out') or account.get('soldOut') or (account.get('inventory') and account.get('inventory', {}).get('remaining') == 0)
    target, stock = account.get('target') or {}, account.get('inventory') or {}
    fields = [{'name':'帳號', 'value':str(account.get('label') or account.get('id') or '未命名')[:100], 'inline':True}]
    if target.get('seq') is not None:
        fields.append({'name':'箱子', 'value':f'BOX-{int(target["seq"]):05d}', 'inline':True})
    ahead = account.get('queueAhead')
    if ahead is not None:
        fields.append({'name':'前方等待', 'value':f'{ahead} 人', 'inline':True})
    if stock.get('remaining') is not None:
        fields.append({'name':'剩餘籤數（網站畫面）', 'value':f'{stock["remaining"]} 枚', 'inline':True})
    prizes = stock.get('prizes') or []
    if prizes:
        fields.append({'name':'各賞剩餘／原始數量', 'value':'　'.join(
            f'{str(p.get("label", ""))[:16]} {p.get("remaining", "—")}/{p.get("total", "—")}' for p in prizes)[:1000]})

    if sold_out:
        title = '📢 籤筒已抽完（售完）'
        auto_resume = account.get('config', {}).get('autoResumeSoldOut', True)
        desc = '目前鎖定的箱子籤數已抽完（售完）。' + ('已自動返回列表重新尋找新開滿箱。' if auto_resume else '請切回專用視窗選擇其他箱子。')
        color = 0xE67E22
    elif event_type == 'entry_passed':
        title = '✅ 已通過入場限制'
        desc = '入場管制已解除，請切回專用視窗選擇商品或籤箱。'
        color = 0x57F287
    elif ready:
        title = '🔔 輪到你了！'
        desc = '請立即切回此帳號的專用視窗，手動繼續購買。'
        color = 0xD7F896
    elif waiting:
        title = '🔔 即將輪到你'
        desc = '已達你設定的等待人數，請準備切回專用視窗。'
        color = 0xFFBE84
    else:
        title = '⚠️ 一番賞助手需要確認'
        desc = '請切回本機總控檢查此帳號的網站訊息；助手不會自動重送排隊。'
        color = 0xFFBE84

    return {'username':'Kuji Desk', 'allowed_mentions':{'parse':[]}, 'embeds':[{
        'title':title,
        'description':desc,
        'color':color,
        'fields':fields,
        'footer':{'text':'Kuji Desk · 庫存以網站畫面為準 · 不含登入資料'},
        'timestamp':datetime.now(timezone.utc).isoformat(),
    }]}


async def send_webhook(session, url, payload):
    """Retry only explicit rate limits; ambiguous sends are never repeated."""
    url = validate_webhook(url)
    for attempt in range(3):
        try:
            async with session.post(url, params={'wait':'true'}, json=payload, allow_redirects=False) as response:
                if response.status in {200, 204}:
                    data = await response.json() if response.status == 200 else {}
                    return {'ok':True, 'message_id':data.get('id'), 'http_status':response.status}
                if response.status == 429:
                    data = await response.json()
                    delay = max(1, min(float(data.get('retry_after', 3)), 60))
                    if attempt < 2:
                        await asyncio.sleep(delay)
                        continue
                return {'ok':False, 'http_status':response.status, 'error':f'Discord 回傳 HTTP {response.status}；未自動重送。'}
        except (aiohttp.ClientError, TimeoutError, ValueError):
            # Never include exception text: it may contain the secret endpoint.
            return {'ok':False, 'error':'Discord 傳送結果不明；未自動重送，請查看頻道。'}
    return {'ok':False, 'error':'Discord 限速，這則通知未確認送達。'}


class Notifier:
    def __init__(self, runtime):
        self.runtime = Path(runtime)
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.runtime / 'discord-events.json'
        try:
            self.ledger = json.loads(self.ledger_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.ledger = {}
        self.status = {'enabled':False, 'connected':False}
        self.stop = False

    def report(self, **values):
        self.status.update(values)
        self.status['checked_at'] = round(time.time()*1000)
        save_json(self.runtime / 'discord-status.json', self.status)

    def config(self):
        try:
            value = json.loads((self.runtime/'discord.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return None
        if not value.get('enabled'):
            return None
        validate_webhook(value.get('webhook_url', ''))
        return value

    async def process(self, accounts, config, session):
        for account in accounts:
            phase=account.get('phase')
            threshold=config.get('ahead_threshold')
            ahead=account.get('queueAhead')
            waiting=(phase=='waiting' and threshold is not None and isinstance(ahead,int)
                     and 0 <= ahead <= int(threshold))
            is_sold_out = bool(account.get('soldOut') or (account.get('inventory') and account.get('inventory', {}).get('remaining') == 0) or '售完' in str(account.get('note', '')))
            sold_out_event = is_sold_out and ('sold_out' in config.get('events', ['ready', 'uncertain', 'sold_out']))
            entry_passed_at = account.get('entryPassedAt')
            entry_passed_event = bool(entry_passed_at) and ('entry_passed' in config.get('events', ['ready', 'uncertain', 'sold_out', 'entry_passed']))

            candidates = []
            if entry_passed_event:
                ep_key = f'{account.get("id")}:entry_passed:{entry_passed_at}'
                if ep_key not in self.ledger:
                    candidates.append(('entry_passed', ep_key))
            if waiting:
                wkey = event_key(account) + ':ahead:' + str(threshold)
                candidates.append(('waiting', wkey))
            elif sold_out_event:
                box_id = str((account.get('target') or {}).get('id') or (account.get('target') or {}).get('seq') or 'box')
                skey = event_key(account) + ':sold_out:' + box_id
                candidates.append(('sold_out', skey))
            elif phase in config.get('events', ['ready', 'uncertain']):
                candidates.append((phase, event_key(account)))

            for event_type, key in candidates:
                if event_type != 'entry_passed' and key in self.ledger:
                    previous = self.ledger[key]
                    interval = max(10, int(config.get('repeat_seconds', 60))) * 1000
                    if (not config.get('repeat_enabled') or previous.get('state') != 'sent'
                            or round(time.time() * 1000) - previous['at'] < interval):
                        continue
                self.ledger[key] = {'state': 'reserved', 'at': round(time.time() * 1000)}
                self.ledger = dict(list(self.ledger.items())[-4000:])
                save_json(self.ledger_path, self.ledger)
                result = await send_webhook(session, config['webhook_url'], payload_for(account, event_type=event_type))
                self.ledger[key].update(state='sent' if result['ok'] else 'unconfirmed')
                save_json(self.ledger_path, self.ledger)
                if result['ok']:
                    self.report(last_success_at=round(time.time()*1000), last_error=None,
                                last_event=f'{account.get("label",account.get("id"))}：{event_type}',
                                message_id=result.get('message_id'))
                else:
                    self.report(last_error=result['error'])
                await asyncio.sleep(1)

    async def run(self):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15),
                headers={'User-Agent':'KujiDesk/1.2 LocalNotifications'}) as session:
            while not self.stop:
                try:
                    config = self.config()
                    if not config:
                        self.report(enabled=False,connected=False)
                        await asyncio.sleep(2)
                        continue
                    auth = json.loads((self.runtime/'panel-session.json').read_text(encoding='utf-8'))
                    async with session.get('http://127.0.0.1:18766/api/state',
                            headers={'Authorization':'Bearer '+auth['token']}, allow_redirects=False) as response:
                        if response.status != 200:
                            self.report(enabled=True,connected=False)
                            await asyncio.sleep(2)
                            continue
                        state = await response.json()
                    self.report(enabled=True, connected=True)
                    await self.process(state.get('accounts',[]), config, session)
                except Exception:
                    self.report(enabled=True, connected=False, poll_error='無法讀取總控或本機設定；會繼續嘗試。')
                await asyncio.sleep(1)


def acquire_lock(runtime):
    path = Path(runtime)/'discord-worker.lock'
    handle = path.open('a+b')
    if path.stat().st_size == 0:
        handle.write(b'0');handle.flush()
    handle.seek(0)
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def spawn_notifier(runtime):
    if not (Path(runtime)/'discord.json').exists():
        return
    probe = acquire_lock(runtime)
    if probe is None:
        return
    probe.close()
    command = ([sys.executable,'--notifier'] if getattr(sys,'frozen',False)
               else [sys.executable,str(Path(__file__).resolve())])
    subprocess.Popen(command+['--runtime',str(runtime)], stdin=subprocess.DEVNULL, env=background_environment(),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime',required=True,type=Path)
    parser.add_argument('--test',action='store_true')
    args=parser.parse_args()
    worker=Notifier(args.runtime)
    if args.test:
        async def test():
            config=worker.config()
            if not config:
                return {'ok':False,'error':'尚未設定 Discord 通知。'}
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15),
                    headers={'User-Agent':'KujiDesk/1.2 LocalNotifications'}) as session:
                result=await send_webhook(session,config['webhook_url'],{
                    'username':'Kuji Desk','allowed_mentions':{'parse':[]},
                    'content':'✅ Kuji Desk 測試通知：Discord 已連接。之後「輪到你」或「需要人工處理」時會在這裡通知，內容包含帳號標籤、箱號與畫面庫存；不會傳送登入資料。'})
                worker.report(test_ok=result['ok'], last_error=result.get('error'),
                    last_success_at=round(time.time()*1000) if result['ok'] else None)
                return result
        print(json.dumps(asyncio.run(test()),ensure_ascii=False))
        return
    handle=acquire_lock(args.runtime)
    if handle is None:
        return
    try:
        (args.runtime/'discord-worker.pid').write_text(str(os.getpid()),encoding='utf-8')
        asyncio.run(worker.run())
    finally:
        handle.close()


if __name__=='__main__':
    main()
