import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch
from aiohttp.test_utils import TestClient, TestServer
from manager import Manager, Account, create_app, list_url, parse_boxes, select_box, validate_config
from details import parse_detail_text


BOXES = '''<ul><li class="selectbox__box-list-item"><span>BOX-94C35</span>
<span class="selectbox__text--product-amount">残70枚</span>
<span class="selectbox__text--product-waiting">2人が順番待ち中</span>
<a class="BOX-00338 94C35B3D5257C400"></a></li>
<li class="selectbox__box-list-item"><span class="selectbox__text--product-amount">残170枚</span>
<a class="BOX-00339 1234567890ABCDEF"></a></li></ul>'''
URL = 'https://on-line.1kuji.com/Form/Product/SelectBox.aspx?pid=sap_0000008694&pno=1'
CONFIG = {'url':URL,'count':70,'minSeconds':2.2,'maxSeconds':4.5}


class ParsingTests(unittest.TestCase):
    def test_visible_personal_queue_and_award_summary(self):
        text = '''等賞一覧 残りくじ70枚
        A賞 2/2 B賞 1/1 C賞 1/1 D賞 1/1 E賞 1/1
        F賞 2/2 G賞 18/18 H賞 8/8 I賞 18/18 J賞 18/18 ラストワン賞
        A賞 残数：1/2 エレン MASTERLISE
残数 70 /70
あと54人であなたの番です'''
        parsed = parse_detail_text(text)
        self.assertEqual(parsed['ahead'],54)
        self.assertEqual(parsed['remaining'],70)
        self.assertEqual(parsed['total'],70)
        self.assertEqual(len(parsed['prizes']),10)
        self.assertEqual(parsed['prizes'][0]['remaining'],2)
        self.assertTrue(parsed['lastOneListed'])

    def test_unknown_and_zero_stock_are_distinct_and_total_waiters_are_not_personal(self):
        parsed=parse_detail_text('残りくじ0枚 A賞 0/2 120人が順番待ち中 ラストワン賞')
        self.assertIsNone(parsed['ahead'])
        self.assertEqual(parsed['remaining'],0)
        self.assertIsNone(parsed['total'])
        self.assertEqual(parsed['prizes'][0]['remaining'],0)
        self.assertIsNone(parse_detail_text('讀取失敗')['remaining'])
        self.assertEqual(parse_detail_text('あと０人であなたの番です')['ahead'],0)
    def test_url_normalizes_html_escaped_query_and_rejects_other_hosts(self):
        self.assertEqual(list_url(URL.replace('&','&amp;'))[0], URL)
        for bad in [URL.replace('on-line.1kuji.com','evil.example'), URL.replace('https:','http:'), URL.replace('SelectBox.aspx','SelectBoxDetail.aspx')]:
            with self.assertRaises(ValueError): list_url(bad)

    def test_hidden_sequence_and_exact_count(self):
        boxes = parse_boxes(BOXES)
        self.assertEqual(select_box(boxes,337,70)['seq'],338)
        self.assertIsNone(select_box(boxes,338,70))
        self.assertEqual(boxes[0]['id'],'94C35B3D5257C400')

    def test_login_or_changed_markup_cannot_be_treated_as_empty_inventory(self):
        with self.assertRaises(ValueError): parse_boxes('<form>ログイン</form>')
        for value in [0,1001]:
            with self.assertRaises(ValueError): validate_config({**CONFIG,'count':value})
        with self.assertRaises(ValueError): validate_config({**CONFIG,'minSeconds':5,'maxSeconds':2.2})


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_stop_cancels_inflight_fetch_without_waiting_or_entering_box(self):
        a=self.a;a.phase='watching';a.config=validate_config(CONFIG);a.baseline=337
        a.page=Mock(url=URL)
        fetching=asyncio.Event()
        async def slow_fetch():
            fetching.set()
            await asyncio.Event().wait()
        a.fetch_boxes=AsyncMock(side_effect=slow_fetch);a.enter_queue=AsyncMock()
        a.task=asyncio.create_task(a.hunt())
        await fetching.wait()
        await asyncio.wait_for(a.stop(),timeout=1)
        self.assertEqual(a.phase,'idle');self.assertIsNone(a.task)
        a.enter_queue.assert_not_awaited()

    async def test_open_existing_window_focuses_without_navigating(self):
        account = self.a
        account.page = Mock(is_closed=Mock(return_value=False), bring_to_front=AsyncMock())
        await account.open(CONFIG)
        account.page.bring_to_front.assert_awaited_once()
        account.page.goto.assert_not_called()

    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.m = Manager(Path(self.temp.name))
        self.a = self.m.accounts['A']

    async def asyncTearDown(self):
        self.temp.cleanup()

    async def test_submission_is_durable_before_click_and_restart_never_retries(self):
        a = self.a
        a.config = validate_config(CONFIG)
        a.target = parse_boxes(BOXES)[0]
        a.phase = 'opening'
        button = Mock()
        button.inner_text = AsyncMock(return_value='正常頁面')
        button.wait_for = AsyncMock()
        button.count = AsyncMock(return_value=1)
        button.is_visible = AsyncMock(return_value=True)
        button.get_attribute = AsyncMock(side_effect=lambda key: a.config['pid'] if key=='data-product-id' else a.target['id'])
        async def click(**kwargs):
            saved=json.loads(a.journal.read_text(encoding='utf-8'))
            self.assertEqual(saved['phase'],'submitting')
            raise RuntimeError('response lost after click')
        button.click = AsyncMock(side_effect=click)
        a.page = Mock(url=URL,goto=AsyncMock(),locator=Mock(return_value=button))
        with self.assertRaises(RuntimeError): await a.enter_queue()
        restored = Account(self.m,'A')
        self.assertEqual(restored.phase,'uncertain')
        self.assertEqual(restored.target,a.target)
        with self.assertRaises(ValueError): await restored.start(CONFIG)
        button.click.assert_awaited_once()
        self.assertEqual(a.page.goto.await_args.kwargs['wait_until'],'domcontentloaded')
        button.wait_for.assert_awaited_once_with(state='visible',timeout=8000)

    async def test_start_uses_visible_baseline_then_immediately_checks_for_new_boxes(self):
        a=self.a;a.phase='idle'
        old=BOXES.replace('00338','00337').replace('00339','00336')
        hidden=Mock(count=AsyncMock(return_value=0))
        a.page=Mock(url=URL,is_closed=Mock(return_value=False),
                    content=AsyncMock(return_value=old),locator=Mock(return_value=hidden))
        a.fetch_boxes=AsyncMock(return_value=parse_boxes(BOXES))
        a.enter_queue=AsyncMock()
        await a.start(CONFIG)
        await asyncio.wait_for(a.task,timeout=1)
        self.assertEqual(a.baseline,337)
        self.assertEqual(a.target['seq'],338)
        a.fetch_boxes.assert_awaited_once()
        a.enter_queue.assert_awaited_once()

    async def test_two_profiles_never_share_job_state(self):
        self.a.phase='waiting';self.a.target=parse_boxes(BOXES)[0];self.a.persist()
        self.assertEqual(self.m.accounts['B'].phase,'closed')
        self.assertFalse(self.m.accounts['B'].journal.exists())
        self.assertEqual(Account(self.m,'A').phase,'uncertain')

    async def test_queue_failure_latches_instead_of_reporting_stale_rank(self):
        a=self.a;a.phase='waiting';a.queue_no=2
        a.socket_message(json.dumps({'Action':'Close'}))
        self.assertTrue(a.queue_alert)
        self.assertEqual(a.phase,'uncertain')

    async def test_real_japanese_waiting_sentence_confirms_queue_and_inventory(self):
        a=self.a;a.phase='uncertain';a.metrics={'submittedAt':1}
        async def evaluate(script):
            a.cancel.set()
            return {'text':'残りくじ70枚 A賞 2/2 あと54人であなたの番です',
                    'ready':False,'number':None,'exitVisible':True,'refreshEnabled':True}
        a.page=Mock(url='https://on-line.1kuji.com/Form/Product/SelectBoxDetail.aspx?pid=sap_0000008694&lbdid=94C35B3D5257C400',is_closed=Mock(return_value=False),evaluate=AsyncMock(side_effect=evaluate))
        await a.observe_queue()
        self.assertEqual(a.phase,'waiting')
        self.assertEqual(a.queue_ahead,54)
        self.assertEqual(a.inventory['remaining'],70)
        self.assertTrue(a.state()['canRequeue'])

    def prepare_requeue(self, fail_confirmation=False):
        a=self.a;a.phase='waiting';a.config=validate_config(CONFIG);a.target=parse_boxes(BOXES)[0]
        exit_button=Mock(count=AsyncMock(return_value=1),is_visible=AsyncMock(return_value=True),click=AsyncMock())
        yes=Mock()
        async def confirm(**kwargs):
            a.page.url=URL
            exit_button.count.return_value=0
        yes.click=AsyncMock(side_effect=confirm)
        dialog=Mock(wait_for=AsyncMock(),inner_text=AsyncMock(return_value='くじ箱選択へ戻りますか？ このページから抜けると順番待ちが解除されます'),get_by_role=Mock(return_value=yes))
        if fail_confirmation:
            dialog.wait_for.side_effect=RuntimeError('confirmation timed out')
        body=Mock(inner_text=AsyncMock(return_value='くじ箱選択'))
        def locator(selector):
            return dialog if selector=='#customConfirm' else body if selector=='body' else exit_button
        async def wait_url(predicate,**kwargs):
            self.assertTrue(predicate(a.page.url))
        a.page=Mock(evaluate=AsyncMock(return_value={'text':'','ready':False,'number':None,'exitVisible':True}), url='https://on-line.1kuji.com/Form/Product/SelectBoxDetail.aspx?pid=sap_0000008694&lbdid=94C35B3D5257C400',
                    is_closed=Mock(return_value=False),locator=Mock(side_effect=locator),
                    wait_for_url=AsyncMock(side_effect=wait_url),wait_for_load_state=AsyncMock(),content=AsyncMock(return_value=BOXES))
        a.start=AsyncMock()
        return exit_button,yes

    async def test_requeue_starts_only_after_confirmed_exit_and_returned_list(self):
        exit_button,yes=self.prepare_requeue()
        await self.a.leave_and_requeue()
        exit_button.click.assert_awaited_once()
        yes.click.assert_awaited_once()
        self.a.start.assert_awaited_once()
        self.a.page.wait_for_url.assert_awaited_once()

    async def test_uncertain_exit_never_restarts_hunt_or_repeats_exit(self):
        exit_button,yes=self.prepare_requeue(fail_confirmation=True)
        with self.assertRaises(ValueError):await self.a.leave_and_requeue()
        self.assertEqual(self.a.phase,'uncertain')
        self.a.start.assert_not_awaited()
        yes.click.assert_not_awaited()
        exit_button.click.assert_awaited_once()

    async def test_explicit_exit_follows_current_box_instead_of_stale_record(self):
        exit_button,yes=self.prepare_requeue()
        self.a.page.url=self.a.page.url.replace('94C35B3D5257C400','FFFFFFFFFFFFFFFF')
        await self.a.leave_and_requeue()
        exit_button.click.assert_awaited_once()
        self.a.start.assert_awaited_once()

    async def test_context_close_clears_stale_connection_only(self):
        a=self.a;a.phase='idle';old=Mock();a.context=old;a.page=Mock()
        a.on_context_closed(old)
        self.assertIsNone(a.context)
        self.assertIsNone(a.page)
        self.assertFalse(a.entry_pending)
        new=Mock();a.context=new
        a.on_context_closed(old)
        self.assertIs(a.context,new)

    async def test_open_cookie_context_closed_can_reopen(self):
        from playwright.async_api import Error as PlaywrightError
        a=self.a;a.phase='closed';a.page=None
        context=Mock(cookies=AsyncMock(side_effect=PlaywrightError('Target closed')),close=AsyncMock())
        a.context=context
        with self.assertRaisesRegex(ValueError,'Chrome'):
            await a.open(CONFIG)
        self.assertIsNone(a.context)
        self.assertIsNone(a.page)
        self.assertFalse(a.entry_pending)
        self.assertEqual(a.phase,'closed')
        context.close.assert_awaited_once()

    async def test_open_uses_visible_chrome_and_separate_account_profile(self):
        a = self.a
        page = Mock(url=URL, goto=AsyncMock(), content=AsyncMock(return_value='<body>首頁</body>'))
        context = Mock(pages=[page], cookies=AsyncMock(return_value=[]))
        launch = AsyncMock(return_value=context)
        a.manager.playwright = Mock(chromium=Mock(launch_persistent_context=launch))
        await a.open(CONFIG)
        args, kwargs = launch.await_args
        self.assertEqual(Path(args[0]), a.manager.runtime / 'profiles-chrome' / a.id)
        self.assertEqual(kwargs['channel'], 'chrome')
        self.assertFalse(kwargs['headless'])
        self.assertIs(a.page, page)

    async def test_open_home_timeout_keeps_browser(self):
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        a=self.a;a.phase='closed';a.page=None
        page=Mock(is_closed=Mock(return_value=False),goto=AsyncMock(side_effect=PlaywrightTimeoutError('slow')))
        a.context=Mock(pages=[page],cookies=AsyncMock(return_value=[]))
        await a.open(CONFIG)
        self.assertIs(a.page,page)
        self.assertEqual(a.phase,'idle')
        self.assertFalse(a.entry_pending)
        self.assertIn('30',a.note)

    async def test_open_home_aborted_preserves_window_in_both_modes(self):
        from playwright.async_api import Error as PlaywrightError
        for login_only in (True, False):
            with self.subTest(login_only=login_only):
                a = Account(self.m, 'B')
                a.phase = 'closed'
                self.m.login_only = login_only
                page = Mock(url='about:blank', goto=AsyncMock(side_effect=PlaywrightError('Page.goto: net::ERR_ABORTED')),
                            is_closed=Mock(return_value=False))
                a.context = Mock(pages=[page], cookies=AsyncMock(return_value=[]))
                await a.open(CONFIG)
                self.assertIs(a.page, page)
                self.assertEqual(a.phase, 'idle')
                self.assertFalse(a.entry_pending)
                self.assertIsNone(a.task)
                self.assertIn('首頁導覽中斷', a.state()['note'])
                page.goto.assert_awaited_once_with('https://on-line.1kuji.com',
                    wait_until='commit' if login_only else 'domcontentloaded', timeout=30000)

    async def test_cancel_observer_interrupts_blocked_page_read(self):
        a=self.a
        entered=asyncio.Event()
        async def blocked():
            entered.set()
            await asyncio.Event().wait()
        a.task=asyncio.create_task(blocked())
        await entered.wait()
        await asyncio.wait_for(a.cancel_observer(),timeout=1)
        self.assertIsNone(a.task)

    async def test_returned_list_clears_stale_rank_even_when_alert_is_latched(self):
        a=self.a;a.phase='waiting';a.config=validate_config(CONFIG)
        a.target=parse_boxes(BOXES)[0];a.queue_no=a.queue_ahead=35
        a.queue_alert=True;a.queue_reason='EndViewing'
        a.page=Mock(content=AsyncMock(return_value=BOXES))
        a.start=AsyncMock()
        ended=await a.reconcile_queue_page({'url':URL,'exitVisible':False,'ahead':None,'number':None})
        self.assertTrue(ended);self.assertEqual(a.phase,'idle')
        self.assertIsNone(a.target);self.assertIsNone(a.queue_ahead)
        self.assertFalse(a.queue_alert)
        a.start.assert_awaited_once_with(a.config)

    async def test_confirmed_soldout_list_restarts_hunt_but_never_reclicks_queue(self):
        a=self.a;a.phase='uncertain';a.config=validate_config(CONFIG)
        a.target=parse_boxes(BOXES)[0];a.queue_reason='SoldOut';a.queue_alert=True
        a.page=Mock(content=AsyncMock(return_value=BOXES));a.start=AsyncMock()
        self.assertTrue(await a.reconcile_queue_page({'url':URL,'ahead':None}))
        a.start.assert_awaited_once()
        self.assertIsNone(a.target)

    async def test_navigation_to_other_product_does_not_restart_old_hunt(self):
        a=self.a;a.phase='uncertain';a.config=validate_config(CONFIG)
        a.queue_reason='SoldOut';a.target=parse_boxes(BOXES)[0]
        a.page=Mock(content=AsyncMock(return_value=BOXES));a.start=AsyncMock()
        await a.reconcile_queue_page({'url':URL.replace('8694','9999'),'ahead':None})
        self.assertEqual(a.phase,'idle');a.start.assert_not_awaited()

    async def test_changed_detail_box_rebinds_without_touching_website(self):
        a=self.a;a.phase='ready';a.config=validate_config(CONFIG)
        a.target=parse_boxes(BOXES)[0];a.queue_alert=True;a.queue_reason='EndViewing';a.queue_ahead=35
        current='https://on-line.1kuji.com/Form/Product/SelectBoxDetail.aspx?pid=sap_0000008694&lbdid=FFFFFFFFFFFFFFFF'
        self.assertFalse(await a.reconcile_queue_page({'url':current}))
        self.assertEqual(a.target['id'],'FFFFFFFFFFFFFFFF')
        self.assertIsNone(a.target['seq']);self.assertIsNone(a.queue_ahead)
        self.assertFalse(a.queue_alert);self.assertEqual(a.phase,'uncertain')

    async def test_already_returned_list_requeue_skips_exit_button(self):
        exit_button,yes=self.prepare_requeue()
        self.a.page.url=URL;exit_button.count.return_value=0
        self.a.page.evaluate.return_value={'text':'くじ箱選択','exitVisible':False,'ready':False,'number':None,'url':URL}
        await self.a.leave_and_requeue()
        exit_button.click.assert_not_awaited();yes.click.assert_not_awaited()
        self.a.start.assert_awaited_once()

    async def test_restarting_one_account_keeps_other_account_job_unchanged(self):
        a=self.a;a.context=Mock(close=AsyncMock());a.open=AsyncMock()
        b=self.m.accounts['B'];b.phase='waiting';b.queue_ahead=17
        await a.restart_account(CONFIG)
        self.assertEqual(b.phase,'waiting');self.assertEqual(b.queue_ahead,17)
        a.open.assert_awaited_once()

    async def test_stock_update_uses_f5_reload_without_clicking_site_buttons(self):
        a=self.a;a.phase='waiting'
        a.page=Mock(url='https://on-line.1kuji.com/Form/Product/SelectBoxDetail.aspx?pid=sap_0000008694&lbdid=FFFFFFFFFFFFFFFF',
                    is_closed=Mock(return_value=False),reload=AsyncMock())
        a.target={'id':'DIFFERENT_OLD_BOX','seq':1}
        a.read_detail=AsyncMock()
        await a.refresh_inventory()
        a.page.reload.assert_awaited_once_with(wait_until='domcontentloaded',timeout=15000)
        a.page.locator.assert_not_called()
        a.read_detail.assert_awaited_once()

    async def test_query_inventory_api_parses_html_and_sets_inventory(self):
        a = self.a
        a.config = {'url': 'https://on-line.1kuji.com/Form/Product/SelectBox.aspx?pid=sap_0000008694&pno=1', 'pid': 'sap_0000008694', 'count': 70, 'minSeconds': 2.2, 'maxSeconds': 4.5, 'autoResumeSoldOut': True}
        a.target = {'id': 'EEB78D33FBBCE1BA', 'seq': 1}
        
        sample_html = '''
        <div class="selectbox-lottery-modal__heading-container">
            <h2>等賞一覧</h2><div><small>残りくじ</small>46枚</div>
        </div>
        <ul class="selectbox-lottery-modal__variation-stock-list">
            <li><span class="variation-stock-prize-name">A賞</span><div><span class="variation-stock-prize-number">1/2</span></div></li>
            <li><span class="variation-stock-prize-name">B賞</span><div><span class="variation-stock-prize-number">0/1</span></div></li>
        </ul>
        <p>あと35人であなたの番です</p>
        '''
        
        class FakeResp:
            status = 200
            async def text(self): return sample_html
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            
        class FakeSession:
            closed = False
            def get(self, url, **kwargs):
                return FakeResp()
                
        a.http_session = FakeSession()
        res = await a.query_inventory_api()
        self.assertEqual(res['remaining'], 46)
        self.assertEqual(res['source'], 'api')
        self.assertEqual(len(res['prizes']), 2)
        self.assertEqual(res['prizes'][0]['label'], 'A賞')
        self.assertEqual(res['prizes'][0]['remaining'], 1)
        self.assertEqual(a.queue_ahead, 35)

    async def test_official_page_reload_retries_observation_without_submission(self):
        a=self.a;a.phase='submitting';a.metrics={'submittedAt':1}
        calls=0
        async def evaluate(script):
            nonlocal calls
            calls+=1
            if calls==1:
                raise RuntimeError('Execution context was destroyed by navigation')
            a.cancel.set()
            return {'ready':False,'number':7}
        a.page=Mock(url='https://on-line.1kuji.com/Form/Product/SelectBoxDetail.aspx?pid=sap_0000008694&lbdid=94C35B3D5257C400',is_closed=Mock(return_value=False),evaluate=AsyncMock(side_effect=evaluate))
        await a.observe_queue()
        self.assertEqual(calls,2)
        self.assertEqual(a.phase,'waiting')
        self.assertEqual(a.queue_no,7)

    async def test_cancellation_after_network_response_prevents_navigation(self):
        a=self.a;a.phase='watching';a.config=validate_config(CONFIG);a.baseline=337
        a.config.update(minSeconds=.001,maxSeconds=.001)
        a.page=Mock(url=URL)
        async def fetch():
            a.cancel.set()
            return parse_boxes(BOXES)
        a.fetch_boxes=AsyncMock(side_effect=fetch)
        a.enter_queue=AsyncMock()
        await a.hunt()
        a.enter_queue.assert_not_awaited()

    async def test_api_auth_origin_guard_and_unrecognized_command(self):
        async with TestClient(TestServer(create_app(self.m))) as client:
            host={'Host':'127.0.0.1:18766'}
            response=await client.get('/api/state',headers=host)
            self.assertEqual(response.status,401)
            auth={**host,'Authorization':'Bearer '+self.m.token}
            response=await client.get('/api/state',headers={**auth,'Origin':'https://evil.example'})
            self.assertEqual(response.status,403)
            response=await client.get('/api/state',headers=auth)
            self.assertEqual(response.status,200)
            self.assertEqual(len((await response.json())['accounts']),3)
            response=await client.post('/api/action',headers=auth,json={'id':'A','action':'eval','code':'anything'})
            self.assertEqual(response.status,400)
            response=await client.get('/manager.py',headers=host)
            self.assertEqual(response.status,404)


    async def test_read_detail_preserves_api_inventory(self):
        a = self.a
        a.inventory = {'remaining': 42, 'total': 70, 'prizes': [], 'source': 'api'}
        a.page = Mock(evaluate=AsyncMock(return_value={
            'text': '残りくじ 60 枚\\nA賞 2 / 2',
            'exitVisible': True,
            'refreshEnabled': True
        }))
        await a.read_detail()
        self.assertEqual(a.inventory['remaining'], 42)
        self.assertEqual(a.inventory['source'], 'api')

    async def test_observe_queue_does_not_rollback_queue_ahead_to_stale_dom(self):
        a = self.a
        a.phase = 'waiting'
        a.queue_ahead = 40
        a.queue_no = 40
        async def evaluate(s):
            a.cancel.set()
            return {'ready': False, 'ahead': 67, 'number': 67, 'text': 'あと67人であなたの番です', 'exitVisible': True}
        a.page = Mock(url='https://on-line.1kuji.com/Form/Product/SelectBoxDetail.aspx?pid=sap_0000008694&lbdid=94C35B3D5257C400',
                      is_closed=Mock(return_value=False),
                      evaluate=AsyncMock(side_effect=evaluate))
        await a.observe_queue()
        self.assertEqual(a.queue_ahead, 40)
        self.assertEqual(a.queue_no, 40)


    async def test_temporary_page_retries_then_stops_on_queue(self):
        from unittest.mock import patch
        body = Mock(inner_text=AsyncMock(side_effect=['一時的にアクセスできません', 'あと5人であなたの番です']))
        normal = Mock(count=AsyncMock(return_value=0))
        self.a.page = Mock(url=URL,locator=Mock(side_effect=lambda selector: body if selector == 'body' else normal),
                           reload=AsyncMock(return_value=None))
        with patch('manager.asyncio.sleep', new_callable=AsyncMock):
            await self.a.wait_temporary_page()
        self.a.page.reload.assert_awaited_once()

    async def test_product_entry_checks_product_and_clicks_once(self):
        a=self.a
        a.config=validate_config(CONFIG)
        entry=Mock(is_visible=AsyncMock(return_value=True), click=AsyncMock())
        buttons=Mock(count=AsyncMock(return_value=1), nth=Mock(return_value=entry))
        role=Mock(or_=Mock(return_value=buttons))
        a.page=Mock(url='https://on-line.1kuji.com/Form/Product/ProductDetail.aspx?pid=sap_0000008694',
                    get_by_role=Mock(return_value=role))
        async def arrive(*args, **kwargs):
            a.page.url=URL
        a.page.wait_for_url=AsyncMock(side_effect=arrive)
        a.wait_temporary_page=AsyncMock()
        a.sync_cookies=AsyncMock()
        self.assertTrue(await a.follow_product_to_list())
        entry.click.assert_awaited_once()
        a.page.url='https://on-line.1kuji.com/Form/Product/ProductDetail.aspx?pid=other'
        with self.assertRaises(ValueError):
            await a.follow_product_to_list()
        self.assertEqual(entry.click.await_count,1)

    async def test_choose_box_entry_submits_once_and_rejects_wrong_box(self):
        a=self.a
        a.config=validate_config(CONFIG)
        a.target=parse_boxes(BOXES)[0]
        from manager import detail_url
        button=Mock(wait_for=AsyncMock(),count=AsyncMock(return_value=1),
                    is_visible=AsyncMock(return_value=True),
                    get_attribute=AsyncMock(return_value='ctl00_ContentPlaceHolder1_lbAddToCart'),
                    inner_text=AsyncMock(return_value='このくじ箱にする'),click=AsyncMock())
        a.page=Mock(url=detail_url(a.config['pid'],a.target),goto=AsyncMock(),locator=Mock(return_value=button))
        a.wait_temporary_page=AsyncMock()
        a.sync_cookies=AsyncMock()
        a.observe_queue=AsyncMock()
        await a.enter_queue()
        button.click.assert_awaited_once()
        self.assertEqual(a.phase,'submitting')
        a.page.url=a.page.url.replace(a.target['id'],'0000000000000000')
        with self.assertRaises(ValueError):await a.enter_queue()
        self.assertEqual(button.click.await_count,1)

    async def test_inventory_skips_monitoring_even_with_stale_box(self):
        a=self.a
        a.phase='watching'
        a.config=validate_config(CONFIG)
        a.target=parse_boxes(BOXES)[0]
        a.http_session=Mock(get=Mock())
        self.assertEqual(await a.query_inventory_api(),{})
        a.http_session.get.assert_not_called()
        a.http_session=None

    async def test_inventory_skips_list_page_with_stale_target(self):
        a=self.a
        a.phase='idle'
        a.config=validate_config(CONFIG)
        a.target=parse_boxes(BOXES)[0]
        a.page=Mock(url=URL,is_closed=Mock(return_value=False))
        a.sync_cookies=AsyncMock()
        self.assertEqual(await a.query_inventory_api(),{})
        a.sync_cookies.assert_not_awaited()

    async def test_list_timeout_recovers_without_queue_submission(self):
        from unittest.mock import patch
        a=self.a;a.phase='watching';a.config=validate_config(CONFIG)
        a.config.update(minSeconds=.001,maxSeconds=.001)
        a.page=Mock(url=URL)
        async def recovered():
            a.cancel.set()
            return []
        a.fetch_boxes=AsyncMock(side_effect=[TimeoutError(), []])
        original=a.fetch_boxes
        async def fetch():
            if original.await_count:
                a.cancel.set()
            return await original()
        a.fetch_boxes=fetch
        a.enter_queue=AsyncMock()
        # Cancel the backoff wait immediately without changing account cancellation.
        async def wait_for(awaitable,timeout):
            awaitable.close()
            raise TimeoutError()
        with patch('manager.asyncio.wait_for',side_effect=wait_for):
            await a.hunt()
        self.assertEqual(original.await_count,2)
        self.assertEqual(a.phase,'watching')
        a.enter_queue.assert_not_awaited()
        self.assertTrue(any('TimeoutError' in e['message'] for e in a.events))

    async def test_soldout_resume_runs_once_and_respects_switch(self):
        a=self.a;a.config=validate_config(CONFIG);a.target=parse_boxes(BOXES)[0]
        a.queue_reason='SoldOut';a.phase='uncertain'
        a.page=Mock(is_closed=Mock(return_value=False));a.leave_and_requeue=AsyncMock()
        a.schedule_soldout_resume();a.schedule_soldout_resume()
        await a.soldout_task
        a.leave_and_requeue.assert_awaited_once()
        a.soldout_attempt=None;a.config['autoResumeSoldOut']=False
        a.schedule_soldout_resume()
        self.assertEqual(a.leave_and_requeue.await_count,1)

    async def test_empty_list_wait_expires_after_one_hour(self):
        from unittest.mock import patch
        a=self.a;a.config=validate_config(CONFIG);a.phase='watching';a.baseline=0
        a.config.update(minSeconds=.001,maxSeconds=.001)
        a.page=Mock(url=URL);a.fetch_boxes=AsyncMock(return_value=[])
        a.enter_queue=AsyncMock()
        ticks=iter([0,3601])
        async def no_wait(awaitable,timeout):
            awaitable.close();raise TimeoutError()
        with patch('manager.time.monotonic',side_effect=lambda:next(ticks,3601)), patch('manager.asyncio.wait_for',side_effect=no_wait):
            await a.hunt()
        self.assertEqual(a.phase,'idle')
        self.assertIn('1小時',a.note)
        a.enter_queue.assert_not_awaited()

    async def test_valid_empty_list_does_not_accept_login_or_challenge(self):
        self.assertEqual(parse_boxes('<h1>くじ箱選択</h1><ul class="selectbox__box-list"></ul>'),[])
        with self.assertRaises(ValueError):parse_boxes('<h1>ログイン</h1><input type="password">')
        with self.assertRaises(ValueError):parse_boxes('<h1>一時的にアクセスを制限</h1>')

    async def test_entry_accepts_product_url_and_no_pid_home(self):
        from manager import entry_url
        product='https://on-line.1kuji.com/Form/Product/ProductDetail.aspx?shop=0&pid=sap_0000008550&bid=IP00006604'
        self.assertEqual(validate_config({**CONFIG,'url':product})['pid'],'sap_0000008550')
        self.assertIsNone(validate_config({**CONFIG,'url':'https://on-line.1kuji.com/'})['pid'])
        with self.assertRaises(ValueError):entry_url('https://on-line.1kuji.com.evil.example/')

    async def test_exact_entry_gate_reloads_despite_heading(self):
        from unittest.mock import patch
        a=self.a
        body=Mock(inner_text=AsyncMock(side_effect=['一時的に入場いただける人数を\n制限しております。','商品情報']))
        other=Mock(count=AsyncMock(return_value=1))
        a.page=Mock(url='https://on-line.1kuji.com/Form/Product/ProductDetail.aspx?pid=sap_0000008550',
                    locator=Mock(side_effect=lambda selector:body if selector=='body' else other),
                    reload=AsyncMock(return_value=None))
        with patch('manager.asyncio.sleep',new_callable=AsyncMock):
            self.assertTrue(await a.wait_temporary_page())
        a.page.reload.assert_awaited_once()

    async def test_gate_without_pid_adopts_product_after_entry(self):
        a=self.a;a.config=validate_config({**CONFIG,'url':'https://on-line.1kuji.com/'})
        a.phase='idle';a.entry_pending=True
        a.page=Mock(url='https://on-line.1kuji.com/',is_closed=Mock(return_value=False),
                    locator=Mock(return_value=Mock(inner_text=AsyncMock(return_value='一時的に入場いただける人数を制限しております。'))))
        async def passed(**kwargs):a.page.url='https://on-line.1kuji.com/Form/Product/ProductDetail.aspx?pid=sap_0000008550'
        a.wait_temporary_page=AsyncMock(side_effect=passed)
        a.follow_product_to_list=AsyncMock()
        a.start=AsyncMock()
        await a.recover_entry()
        self.assertEqual(a.config['pid'],'sap_0000008550')
        a.follow_product_to_list.assert_awaited_once()
        a.start.assert_awaited_once()

    async def test_recovery_stop_cancels_reload_worker(self):
        a=self.a;a.phase='recovering';a.entry_pending=True
        a.task=asyncio.create_task(asyncio.Event().wait())
        await a.stop()
        self.assertFalse(a.entry_pending)
        self.assertEqual(a.phase,'idle')

    async def test_start_returns_while_entry_waits_in_background(self):
        a=self.a;a.phase='idle'
        a.page=Mock(is_closed=Mock(return_value=False),url='https://on-line.1kuji.com/Form/Product/ProductDetail.aspx?pid=sap_0000008550')
        a.recover_entry=AsyncMock(side_effect=asyncio.Event().wait)
        await asyncio.wait_for(a.start({**CONFIG,'url':a.page.url}),timeout=.2)
        self.assertEqual(a.phase,'recovering')
        self.assertFalse(a.task.done())
        await a.stop()
        self.assertEqual(a.phase,'idle')

    async def test_stop_api_does_not_wait_for_entry_lock(self):
        a=self.a;a.phase='recovering';a.entry_pending=True
        entered=asyncio.Event()
        async def blocked():
            async with a.lock:
                entered.set()
                await asyncio.Event().wait()
        a.task=asyncio.create_task(blocked());await entered.wait()
        async with TestClient(TestServer(create_app(self.m))) as client:
            headers={'Host':'127.0.0.1:18766','Authorization':'Bearer '+self.m.token}
            response=await asyncio.wait_for(client.post('/api/action',headers=headers,json={'id':'A','action':'stop'}),timeout=.5)
            self.assertEqual(response.status,200)
            self.assertEqual(a.phase,'idle')

    async def test_login_only_reuses_window_when_control_resumes(self):
        self.m.login_only = True
        a = self.a
        a.phase = 'uncertain'
        a.target = parse_boxes(BOXES)[0]
        a.config = validate_config(CONFIG)
        page = Mock(url=URL, is_closed=Mock(return_value=False), goto=AsyncMock())
        a.context = Mock(pages=[page], cookies=AsyncMock(return_value=[]), close=AsyncMock())
        self.m.playwright = Mock(stop=AsyncMock())
        a.begin_entry = Mock()
        a.observe_queue = AsyncMock()
        a.start = AsyncMock()
        headers = {'Host':'127.0.0.1:18766', 'Authorization':'Bearer '+self.m.token}
        async with TestClient(TestServer(create_app(self.m)), headers=headers) as client:
            response = await client.post('/api/action', json={'id':'A','action':'open'})
            self.assertEqual(response.status, 200)
            shown = (await response.json())['account']
            self.assertEqual(shown['phase'], 'idle')
            self.assertTrue(shown['opened'])
            self.assertEqual(page.goto.await_args.args[0], 'https://on-line.1kuji.com')
            self.assertFalse(a.entry_pending)
            self.assertEqual(a.phase, 'uncertain')
            self.assertIsNone(a.task)

            for action in ('start','requeue','inspect','api_inventory'):
                response = await client.post('/api/action', json={'id':'A','action':action})
                self.assertEqual(response.status, 400)
            with patch('manager.spawn_notifier') as notifier:
                response = await client.post('/api/control', json={'action':'resume'})
            self.assertEqual(response.status, 200)
            notifier.assert_called_once_with(self.m.runtime)
            self.assertFalse(self.m.login_only)
            self.assertIs(a.page, page)
            a.start.assert_not_awaited()
            a.begin_entry.assert_not_called()
            a.observe_queue.assert_not_awaited()
            response = await client.post('/api/action', json={'id':'A','action':'start',**CONFIG})
            self.assertEqual(response.status, 200)
            a.start.assert_awaited_once()

    async def test_restart_api_cancels_entry_before_waiting_for_account_lock(self):
        a=self.a;a.phase='recovering';a.entry_pending=True
        entered=asyncio.Event()
        async def blocked():
            async with a.lock:
                entered.set()
                await asyncio.Event().wait()
        a.task=asyncio.create_task(blocked());await entered.wait()
        a.restart_account=AsyncMock()
        self.m.playwright=Mock(stop=AsyncMock())
        async with TestClient(TestServer(create_app(self.m))) as client:
            headers={'Host':'127.0.0.1:18766','Authorization':'Bearer '+self.m.token}
            response=await asyncio.wait_for(client.post('/api/action',headers=headers,
                json={'id':'A','action':'restart','confirmed':True}),timeout=.5)
            self.assertEqual(response.status,200)
        a.restart_account.assert_awaited_once()
        self.assertFalse(a.entry_pending)
        self.assertIsNone(a.task)

    async def test_entry_gate_uses_config_jitter_beyond_100_attempts(self):
        from unittest.mock import patch
        a=self.a;a.config={**validate_config(CONFIG),'minSeconds':7,'maxSeconds':9}
        body=Mock(inner_text=AsyncMock(side_effect=['一時的に入場いただける人数を制限しております。']*101+['商品情報']))
        other=Mock(count=AsyncMock(return_value=0))
        a.page=Mock(url='https://on-line.1kuji.com/Form/Product/ProductDetail.aspx?pid=p',
                    locator=Mock(side_effect=lambda selector:body if selector=='body' else other),reload=AsyncMock(return_value=None))
        with patch('manager.random.uniform',return_value=8) as jitter, patch('manager.asyncio.sleep',new_callable=AsyncMock) as sleep:
            await a.wait_temporary_page(entry_only=True)
        self.assertEqual(a.page.reload.await_count,101)
        jitter.assert_called_with(7,9)
        self.assertTrue(all(call.args==(8,) for call in sleep.await_args_list))

    async def test_entry_refresh_switch_disables_reloads(self):
        cfg_true = validate_config({**CONFIG})
        self.assertTrue(cfg_true['entryRefresh'])
        cfg_false = validate_config({**CONFIG, 'entryRefresh': False})
        self.assertFalse(cfg_false['entryRefresh'])

        a = self.a
        a.config = cfg_false
        body = Mock(inner_text=AsyncMock(return_value='一時的に入場いただける人数を制限しております。'))
        other = Mock(count=AsyncMock(return_value=0))
        a.page = Mock(url='https://on-line.1kuji.com/', is_closed=Mock(return_value=False),
                      locator=Mock(side_effect=lambda selector: body if selector == 'body' else other),
                      reload=AsyncMock())
        # When entryRefresh is False, wait_temporary_page should return False and never call reload
        result = await a.wait_temporary_page()
        self.assertFalse(result)
        a.page.reload.assert_not_awaited()
        self.assertIn('已關閉自動入場刷新', a.note)

if __name__ == '__main__': unittest.main()
