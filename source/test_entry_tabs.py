import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

from manager import CloudflarePaused, Manager


class EntryTabsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.manager = Manager(Path(self.temp.name))
        self.a = self.manager.accounts['A']
        self.url = 'https://on-line.1kuji.com/Form/Product/ProductDetail.aspx?pid=test'
        self.original = self.page()
        self.extras = [self.page() for _ in range(4)]
        self.manual = self.page()
        self.a.page = self.original
        self.a.context = Mock(new_page=AsyncMock(side_effect=self.extras))
        self.a.navigate_entry_page = AsyncMock()

    def page(self):
        return Mock(url=self.url, close=AsyncMock(), on=Mock(), remove_listener=Mock())

    async def asyncTearDown(self):
        self.temp.cleanup()

    async def test_first_admitted_tab_wins_and_only_owned_losers_close(self):
        async def wait(*, entry_only, page):
            if page is self.extras[0]:return True
            await asyncio.Event().wait()
        self.a.wait_temporary_page = AsyncMock(side_effect=wait)
        await self.a.wait_entry_tabs()
        self.assertIs(self.a.page, self.extras[0])
        self.assertEqual(self.a.context.new_page.await_count, 4)
        self.extras[0].close.assert_not_awaited()
        self.original.close.assert_awaited_once()
        for page in self.extras[1:]:page.close.assert_awaited_once()
        self.manual.close.assert_not_awaited()
        self.original.remove_listener.assert_any_call('close',self.a.on_closed)

    async def test_cancellation_closes_extras_and_keeps_original(self):
        entered=asyncio.Event()
        async def wait(**kwargs):
            entered.set()
            await asyncio.Event().wait()
        self.a.wait_temporary_page=AsyncMock(side_effect=wait)
        task=asyncio.create_task(self.a.wait_entry_tabs())
        await entered.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):await task
        self.original.close.assert_not_awaited()
        for page in self.extras:page.close.assert_awaited_once()

    async def test_cloudflare_stops_admission_and_closes_extra_tabs(self):
        async def wait(*, entry_only, page):
            if page is self.original:
                self.a.check_cloudflare('正在執行安全驗證 Cloudflare')
            await asyncio.Event().wait()
        self.a.wait_temporary_page = AsyncMock(side_effect=wait)
        with self.assertRaises(CloudflarePaused):
            await asyncio.wait_for(self.a.wait_entry_tabs(), timeout=1)
        self.assertTrue(self.a.cancel.is_set())
        self.assertTrue(self.a.cloudflare_paused)
        self.assertEqual(self.a.phase, 'idle')
        self.original.close.assert_not_awaited()
        for page in self.extras:
            page.close.assert_awaited_once()

    async def test_wrong_product_cannot_win(self):
        self.extras[0].url=self.url.replace('test','other')
        async def wait(*, entry_only, page):
            if page is self.extras[1]:await asyncio.sleep(.01);return True
            if page is self.extras[0]:return True
            await asyncio.Event().wait()
        self.a.wait_temporary_page=AsyncMock(side_effect=wait)
        await self.a.wait_entry_tabs()
        self.assertIs(self.a.page,self.extras[1])
        self.extras[0].close.assert_awaited_once()


class EntryCooldownTests(unittest.IsolatedAsyncioTestCase):
    async def test_429_cooldown_applies_to_next_tab_request(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Manager(Path(temp)).accounts['A']
            a.config={'minSeconds':2.2,'maxSeconds':3}
            page1=Mock(reload=AsyncMock(return_value=Mock(status=429,headers={'retry-after':'60'})))
            page2=Mock(reload=AsyncMock(return_value=None))
            with patch('manager.asyncio.sleep',new_callable=AsyncMock) as sleep:
                await a.navigate_entry_page(page1)
                await a.navigate_entry_page(page2)
            self.assertGreater(sleep.await_args_list[-1].args[0],59)
            page2.reload.assert_awaited_once()


class IndependentRefreshTests(unittest.IsolatedAsyncioTestCase):
    async def test_five_requests_use_distinct_jitter_and_overlap(self):
        with tempfile.TemporaryDirectory() as temp:
            a=Manager(Path(temp)).accounts['A']
            a.config={'minSeconds':2.2,'maxSeconds':3}
            delays=[];entered=0;all_entered=asyncio.Event()
            real_sleep=asyncio.sleep
            async def sleep(seconds):
                delays.append(seconds)
                await real_sleep(0)
            async def reload(**kwargs):
                nonlocal entered
                entered+=1
                if entered==5:all_entered.set()
                await all_entered.wait()
            pages=[Mock(reload=AsyncMock(side_effect=reload)) for _ in range(5)]
            with patch('manager.random.uniform',side_effect=[2.2,2.4,2.6,2.8,3]) as jitter, patch('manager.asyncio.sleep',side_effect=sleep):
                await asyncio.wait_for(asyncio.gather(*(a.navigate_entry_page(p) for p in pages)),timeout=1)
            self.assertEqual(delays,[2.2,2.4,2.6,2.8,3])
            self.assertEqual(entered,5)
            self.assertEqual(jitter.call_count,5)
            jitter.assert_called_with(2.2,3)


if __name__=='__main__':unittest.main()
