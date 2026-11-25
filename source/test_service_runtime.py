import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import manager
import service_runtime


class ServiceRuntimeTests(unittest.TestCase):
    def test_uses_only_authenticated_running_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            registry=Path(temp)/'active.json'
            preferred=Path(temp)/'new'
            active=Path(temp)/'active'
            registry.write_text(json.dumps({'runtime':str(active)}),encoding='utf-8')
            with patch('service_runtime.registry_file',return_value=registry):
                self.assertEqual(service_runtime.resolve_runtime(preferred,lambda p:p==active),active)
                self.assertEqual(service_runtime.resolve_runtime(preferred,lambda p:False),preferred)

    def test_stale_or_corrupt_registry_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            registry=Path(temp)/'active.json';registry.write_text('broken')
            preferred=Path(temp)/'new'
            with patch('service_runtime.registry_file',return_value=registry):
                self.assertEqual(service_runtime.resolve_runtime(preferred,lambda p:False),preferred)

    def test_port_reservation_prevents_second_listener(self):
        listener=service_runtime.bind_listener(0)
        try:
            self.assertIsNone(service_runtime.bind_listener(listener.getsockname()[1]))
        finally:listener.close()

    def test_restart_updates_existing_login_only_service_without_enabling_control(self):
        from native_ui import Client
        client = Client(Path('.'))
        with patch.object(client, 'alive', side_effect=[{'version':'1.5.17', 'loginOnly':True}, None]), \
             patch.object(client, 'call') as call, patch.object(client, 'ensure_server') as ensure:
            client.restart_server()
        call.assert_called_once_with('control', {'action':'shutdown', 'confirmed':True})
        ensure.assert_called_once_with(login_only=True)

    def test_duplicate_start_never_overwrites_session_or_constructs_manager(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime=Path(temp)
            session=runtime/'panel-session.json'
            session.write_text('{"token":"test-only-existing"}')
            with patch('sys.argv',['manager','--runtime',temp,'--no-browser']), patch('manager.urlopen',side_effect=OSError()), patch('manager.bind_listener',return_value=None), patch('manager.Manager') as create, patch('manager.spawn_notifier') as notify:
                manager.main()
            self.assertEqual(json.loads(session.read_text())['token'],'test-only-existing')
            create.assert_not_called();notify.assert_not_called()


if __name__=='__main__':unittest.main()
