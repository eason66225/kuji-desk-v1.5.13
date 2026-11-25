import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch
import aiohttp
from notifications import Notifier, event_key, payload_for, send_webhook, validate_webhook


ACCOUNT={'id':'A','label':'帳號 A','phase':'ready','target':{'id':'94C35B3D5257C400','seq':338},
         'metrics':{'startedAt':1234,'readyAt':5678},'queueAhead':0,
         'inventory':{'remaining':70,'prizes':[{'label':'A賞','remaining':2,'total':2}]}}
WEBHOOK='https://discord.com/api/webhooks/123456/test-token'


class Response:
    def __init__(self,status,data):self.status,self.data=status,data
    async def __aenter__(self):return self
    async def __aexit__(self,*args):pass
    async def json(self):return self.data


class NotificationTests(unittest.IsolatedAsyncioTestCase):
    async def test_sold_out_notification(self):
        with tempfile.TemporaryDirectory() as folder:
            worker = Notifier(folder)
            config = {'webhook_url': WEBHOOK, 'events': ['ready', 'uncertain', 'sold_out']}
            account = {**ACCOUNT, 'phase': 'uncertain', 'soldOut': True, 'inventory': {'remaining': 0}}
            sent_payloads = []
            async def mock_send(session, url, payload):
                sent_payloads.append(payload)
                return {'ok': True, 'message_id': '99'}
            with patch('notifications.send_webhook', new=AsyncMock(side_effect=mock_send)), patch('notifications.asyncio.sleep', new=AsyncMock()):
                await worker.process([account], config, None)
                self.assertEqual(len(sent_payloads), 1)
                self.assertIn('籤筒已抽完', sent_payloads[0]['embeds'][0]['title'])
                # Deduplication check
                await worker.process([account], config, None)
                self.assertEqual(len(sent_payloads), 1)

    async def test_entry_passed_notification(self):
        with tempfile.TemporaryDirectory() as folder:
            worker = Notifier(folder)
            config = {'webhook_url': WEBHOOK, 'events': ['entry_passed']}
            account = {**ACCOUNT, 'phase': 'idle', 'entryPassedAt': 987654}
            sent_payloads = []
            async def mock_send(session, url, payload):
                sent_payloads.append(payload)
                return {'ok': True, 'message_id': '101'}
            with patch('notifications.send_webhook', new=AsyncMock(side_effect=mock_send)), patch('notifications.asyncio.sleep', new=AsyncMock()):
                await worker.process([account], config, None)
                self.assertEqual(len(sent_payloads), 1)
                self.assertIn('可進入商品／籤箱頁', sent_payloads[0]['embeds'][0]['title'])
                # Deduplication check with same entryPassedAt
                await worker.process([account], config, None)
                self.assertEqual(len(sent_payloads), 1)
                # Different entryPassedAt should notify again
                account['entryPassedAt'] = 987655
                await worker.process([account], config, None)
                self.assertEqual(len(sent_payloads), 2)

    async def test_threshold_repeat_interval_and_unknown_rank(self):
        with tempfile.TemporaryDirectory() as folder:
            worker=Notifier(folder)
            config={'webhook_url':WEBHOOK,'events':[],'ahead_threshold':5,
                    'repeat_enabled':True,'repeat_seconds':60}
            account={**ACCOUNT,'phase':'waiting','queueAhead':6}
            with patch('notifications.send_webhook',new=AsyncMock(return_value={'ok':True})) as send,patch('notifications.asyncio.sleep',new=AsyncMock()),patch('notifications.time.time',return_value=1000) as clock:
                await worker.process([account],config,None)
                await worker.process([{**account,'queueAhead':None}],config,None)
                send.assert_not_awaited()
                account['queueAhead']=5
                await worker.process([account],config,None)
                clock.return_value=1059
                await Notifier(folder).process([{**account,'queueAhead':3}],config,None)
                self.assertEqual(send.await_count,1)
                clock.return_value=1060
                await Notifier(folder).process([account],config,None)
                self.assertEqual(send.await_count,2)
                clock.return_value=1200
                await worker.process([account],{**config,'repeat_enabled':False},None)
                self.assertEqual(send.await_count,2)

    def test_endpoint_validation_and_payload_do_not_expose_credentials(self):
        self.assertEqual(validate_webhook(WEBHOOK),WEBHOOK)
        for bad in [WEBHOOK.replace('discord.com','other.example'),WEBHOOK.replace('https:','http:'),WEBHOOK+'?token=secret']:
            with self.assertRaises(ValueError):validate_webhook(bad)
        payload=payload_for({**ACCOUNT,'note':'secret cookie hidden here'})
        self.assertEqual(payload['allowed_mentions'],{'parse':[]})
        self.assertNotIn('secret cookie',json.dumps(payload))
        self.assertIn('70',json.dumps(payload))

    def test_ready_timestamp_updates_do_not_create_duplicate_alerts_for_same_job(self):
        self.assertEqual(event_key(ACCOUNT),event_key({**ACCOUNT,'metrics':{'startedAt':1234,'readyAt':9999}}))
        self.assertNotEqual(event_key(ACCOUNT),event_key({**ACCOUNT,'metrics':{'startedAt':9999}}))

    async def test_dedup_survives_worker_restart_and_ignores_waiting_phase(self):
        with tempfile.TemporaryDirectory() as folder:
            worker=Notifier(folder)
            async def delivered(session,url,payload):
                ledger=json.loads((Path(folder)/'discord-events.json').read_text(encoding='utf-8'))
                self.assertEqual(ledger[event_key(ACCOUNT)]['state'],'reserved')
                return {'ok':True,'message_id':'42'}
            with patch('notifications.send_webhook',new=AsyncMock(side_effect=delivered)) as send,patch('notifications.asyncio.sleep',new=AsyncMock()):
                config={'webhook_url':WEBHOOK,'events':['ready','uncertain']}
                await worker.process([ACCOUNT,{**ACCOUNT,'id':'B','phase':'waiting'}],config,None)
                await Notifier(folder).process([ACCOUNT],config,None)
                self.assertEqual(send.await_count,1)

    async def test_only_explicit_rate_limit_is_retried(self):
        session=Mock(post=Mock(side_effect=[Response(429,{'retry_after':1}),Response(200,{'id':'42'})]))
        with patch('notifications.asyncio.sleep',new=AsyncMock()):
            result=await send_webhook(session,WEBHOOK,payload_for(ACCOUNT))
        self.assertTrue(result['ok'])
        self.assertEqual(session.post.call_count,2)
        session=Mock(post=Mock(side_effect=aiohttp.ClientConnectionError(WEBHOOK)))
        result=await send_webhook(session,WEBHOOK,payload_for(ACCOUNT))
        self.assertFalse(result['ok'])
        self.assertNotIn(WEBHOOK,json.dumps(result))
        self.assertEqual(session.post.call_count,1)

    async def test_ambiguous_send_is_reserved_and_not_resent_after_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch('notifications.send_webhook',new=AsyncMock(return_value={'ok':False,'error':'結果不明'})) as send,patch('notifications.asyncio.sleep',new=AsyncMock()):
                config={'webhook_url':WEBHOOK}
                await Notifier(folder).process([ACCOUNT],config,None)
                await Notifier(folder).process([ACCOUNT],config,None)
                self.assertEqual(send.await_count,1)
