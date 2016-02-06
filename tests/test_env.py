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
        host, port, user, pass_, path = client.get_auth_from_env()
        self.assertEqual('192.168.1.1', host)
        self.assertEqual(6443, port)
        self.assertEqual('user', user)
        self.assertEqual('pass', pass_)

    @mock.patch('os.getenv')
    def test_get_separate(self, mock_getenv):
        mock_getenv.side_effect = self.FAKE_ENV2.get
        host, port, user, pass_, path = client.get_auth_from_env()
        self.assertEqual('192.168.1.2', host)
        self.assertEqual(6443, port)
        self.assertEqual('user', user)
        self.assertEqual('pass', pass_)
