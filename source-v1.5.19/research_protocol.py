"""Read authenticated page scripts and passively capture JSON; no queue submission."""
import asyncio
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

async def main():
    runtime=Path(__file__).resolve().parents[2]/'Runtime'/'kuji-manager'
    output=runtime/'api-research';output.mkdir(exist_ok=True)
    accounts=json.loads((output/'account-state.json').read_text(encoding='utf-8'))
    account=next(a for a in accounts if a['id']=='B')
    messages=[];index=[]
    async with async_playwright() as p:
        context=await p.chromium.launch_persistent_context(str(runtime/'profiles'/'B'),channel='chrome',headless=False,no_viewport=True)
        try:
            page=context.pages[0] if context.pages else await context.new_page()
            def socket(ws):
                if 'LotteryBoxQueue' in ws.url:
                    ws.on('framereceived',lambda value:messages.append({'direction':'received','data':value}))
                    ws.on('framesent',lambda value:messages.append({'direction':'sent','data':value}))
            page.on('websocket',socket)
            config=account.get('config') or {}
            urls=[config.get('url')]
            target=account.get('target') or {}
            if target.get('id') and config.get('pid'):
                from manager import detail_url
                urls.append(detail_url(config['pid'],target))
            seen=set()
            for number,url in enumerate(filter(None,urls)):
                await page.goto(url,wait_until='domcontentloaded',timeout=30000)
                if urlparse(page.url).netloc != 'on-line.1kuji.com' or '/Login' in page.url:
                    print('Waiting for manual login in account B window',flush=True)
                    for _ in range(1800):
                        if page.is_closed():raise RuntimeError('Login window closed')
                        if (urlparse(page.url).netloc=='on-line.1kuji.com'
                                and urlparse(page.url).path.startswith('/Form/Product/')):break
                        await asyncio.sleep(.5)
                    else:raise RuntimeError('Manual login timed out')
                    await page.goto(url,wait_until='domcontentloaded',timeout=30000)
                await page.wait_for_timeout(2500)
                (output/f'page-{number}.html').write_text(await page.content(),encoding='utf-8')
                scripts=await page.locator('script[src]').evaluate_all('(nodes)=>nodes.map(n=>n.src)')
                index.append({'page':number,'url':page.url,'scripts':scripts})
                for source in scripts:
                    if urlparse(source).netloc!='on-line.1kuji.com' or source in seen:continue
                    seen.add(source)
                    response=await context.request.get(source)
                    if response.ok:
                        name=f'script-{len(seen):02d}.js'
                        (output/name).write_text(await response.text(),encoding='utf-8')
                        index.append({'file':name,'source':source})
                    await response.dispose()
            (output/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
            (output/'websocket.json').write_text(json.dumps(messages,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'pages':len([x for x in index if 'page' in x]),'scripts':len(seen),'socket_frames':len(messages)}))
        finally:
            await context.close()

if __name__=='__main__':asyncio.run(main())
