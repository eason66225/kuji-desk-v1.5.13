"""Keep the user's B research window open until they close it themselves."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    runtime=Path(__file__).resolve().parents[2]/'Runtime'/'kuji-manager'
    accounts=json.loads((runtime/'api-research'/'account-state.json').read_text(encoding='utf-8'))
    account=next(a for a in accounts if a['id']=='B')
    from manager import detail_url
    async with async_playwright() as p:
        context=await p.chromium.launch_persistent_context(str(runtime/'profiles'/'B'),channel='chrome',headless=False,no_viewport=True)
        page=context.pages[0] if context.pages else await context.new_page()
        closed=asyncio.Event()
        context.on('close',lambda *_:closed.set())
        try:
            await page.goto(account['config']['url'],wait_until='domcontentloaded')
        except Exception:
            print('Window kept open; navigation interrupted',flush=True)
        print('Account B window stays open until user closes it',flush=True)
        await closed.wait()

if __name__=='__main__':asyncio.run(main())
