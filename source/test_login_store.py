import tempfile
import time
import unittest
from pathlib import Path

import login_store


class LoginStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'A.bin'
        self.cookie = {'name':'session', 'value':'test-secret-only',
                       'domain':'on-line.1kuji.com', 'path':'/', 'expires':-1,
                       'httpOnly':True, 'secure':True, 'sameSite':'Lax'}

    def tearDown(self):
        self.temp.cleanup()

    def test_encrypted_roundtrip_and_no_plaintext(self):
        login_store.save(self.path, [self.cookie])
        self.assertNotIn(b'test-secret-only', self.path.read_bytes())
        self.assertEqual(login_store.restore(self.path, []), [self.cookie])

    def test_preserves_newer_cookie_and_account_isolation(self):
        login_store.save(self.path, [self.cookie])
        self.assertEqual(login_store.restore(self.path, [dict(self.cookie,value='newer')]), [])
        self.assertEqual(login_store.restore(self.path.with_name('B.bin'), []), [])

    def test_expired_and_other_domains_are_excluded(self):
        login_store.save(self.path, [self.cookie,
            dict(self.cookie,name='expired',expires=time.time()-60),
            dict(self.cookie,name='external',domain='example.com')])
        self.assertEqual(login_store.restore(self.path, []), [self.cookie])

    def test_corrupted_snapshot_is_rejected(self):
        self.path.write_bytes(b'corrupt')
        with self.assertRaises(OSError):
            login_store.restore(self.path, [])


if __name__ == '__main__':
    unittest.main()
