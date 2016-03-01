import unittest

import mock

from mficlient import client


class TestCliUtils(unittest.TestCase):
    FAKE_ENV1 = {
        'MFI': 'http://user:pass@192.168.1.1:6443',
    }

    FAKE_ENV2 = {
        'MFI_HOST': '192.168.1.2',
        'MFI_PORT': '6443',
        'MFI_USER': 'user',
        'MFI_PASS': 'pass',
    }

    @mock.patch('os.getenv')
    def test_get_auth_combined(self, mock_getenv):
        mock_getenv.side_effect = self.FAKE_ENV1.get
        host, port, user, pass_, path, tls = client.get_auth_from_env()
        self.assertEqual('192.168.1.1', host)
        self.assertEqual(6443, port)
        self.assertEqual('user', user)
        self.assertEqual('pass', pass_)
        self.assertFalse(tls)

    @mock.patch('os.getenv')
    def test_get_auth_combined_tls(self, mock_getenv):
        tls_env = dict(self.FAKE_ENV1)
        tls_env['MFI'] = tls_env['MFI'].replace('http://', 'https://')
        mock_getenv.side_effect = tls_env.get
        host, port, user, pass_, path, tls = client.get_auth_from_env()
        self.assertEqual('192.168.1.1', host)
        self.assertEqual(6443, port)
        self.assertEqual('user', user)
        self.assertEqual('pass', pass_)
        self.assertTrue(tls)

    @mock.patch('os.getenv')
    def test_get_separate(self, mock_getenv):
        mock_getenv.side_effect = self.FAKE_ENV2.get
        host, port, user, pass_, path, tls = client.get_auth_from_env()
        self.assertEqual('192.168.1.2', host)
        self.assertEqual(6443, port)
        self.assertEqual('user', user)
        self.assertEqual('pass', pass_)
        self.assertFalse(tls)
