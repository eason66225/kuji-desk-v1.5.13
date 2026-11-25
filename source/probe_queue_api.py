"""Read-only JSON queue probe, with Chrome closed before HTTP requests."""
import asyncio
import json
import re
from pathlib import Path
import aiohttp
from playwright.async_api import async_playwright

async def main():
    runtime=Path(__file__).resolve().parents[2]/'Runtime'/'kuji-manager'
    folder=runtime/'api-research'
    state=json.loads((folder/'account-state.json').read_text(encoding='utf-8'))
    account=next(a for a in state if a['id']=='B')
    config=account['config'];target=account['target']
    from manager import detail_url
    url=detail_url(config['pid'],target)
    async with async_playwright() as p:
        context=await p.chromium.launch_persistent_context(str(runtime/'profiles'/'B'),channel='chrome',headless=False)
        try:
            page=context.pages[0]
            await page.goto(url,wait_until='domcontentloaded')
            print('Waiting for account B login if needed',flush=True)
            for _ in range(1800):
                if page.is_closed():raise RuntimeError('Login window closed')
                if '/Form/Product/' in page.url and 'on-line.1kuji.com'==__import__('urllib.parse',fromlist=['urlparse']).urlparse(page.url).netloc:break
                await asyncio.sleep(.5)
            else:raise RuntimeError('Login timed out')
            cookies=await context.cookies(['https://on-line.1kuji.com'])
        finally:await context.close()
    # Cookies stay in memory; do not write credentials to research artifacts.
    async with aiohttp.ClientSession(cookies={c['name']:c['value'] for c in cookies},
            timeout=aiohttp.ClientTimeout(total=20),headers={'User-Agent':'Mozilla/5.0'}) as session:
        async with session.get(url) as response:
            html=await response.text()
            (folder/'http-detail.html').write_text(html,encoding='utf-8')
            print(json.dumps({'detail_status':response.status,'detail_path':response.url.path,'cookie_count':len(cookies)}))
            if response.url.host!='on-line.1kuji.com':raise RuntimeError('Login required')
        user=re.search(r"userId\s*:\s*'([^']+)'",html)
        if not user:raise RuntimeError('Account identity missing; no API call sent')
        body={'userId':user[1],'productId':config['pid'],'hashedDisplayId':target['id']}
        endpoint='https://on-line.1kuji.com/Form/Product/SelectBoxDetail.aspx/GetLotteryBoxWaitCount'
        async with session.post(endpoint,json=body,headers={'Origin':'https://on-line.1kuji.com','Referer':url}) as response:
            data=await response.json(content_type=None)
            (folder/'queue-read-response.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
            result=data.get('d',{})
            if isinstance(result,str):
                try:result=json.loads(result)
                except ValueError:result={}
            print(json.dumps({'http_status':response.status,'response_keys':list(data),
                'fields':list(result) if isinstance(result,dict) else [],
                'waiting_no':result.get('your_waiting_no') if isinstance(result,dict) else None,
                'browser_closed_during_request':True},ensure_ascii=False))

if __name__=='__main__':asyncio.run(main())
