import json
import unittest

import mock

from mficlient import client
from mficlient import fake


class TestMFiClientWithFakeData(unittest.TestCase):
    def test_get_port(self):
        client = fake.FakeMFiClient()
        port = client.get_port(label='Relay Control')
        self.assertEqual('Output 12v', port.model)
        self.assertEqual('Relay Control', port.label)
        self.assertEqual('5650b1f29e1141bc88ed29f9', port.ident)
        self.assertTrue(isinstance(port.data, dict))

    def test_get_devices(self):
        client_ = fake.FakeMFiClient()
        devs = client_.get_devices()
        found_port = False
        for device in devs:
            self.assertTrue(hasattr(device, 'ports'))
            self.assertTrue(isinstance(device, client.Device))
            for ident, port in device.ports.items():
                self.assertEqual(ident, port.ident)
                self.assertTrue(isinstance(port, client.Port))
                if port.label == 'Relay Control':
                    found_port = True

    def test_control_port(self):
        client = fake.FakeMFiClient()
        port = client.get_port(label='Relay Control')
        self.assertEqual(0.0, port.output)
        port.control(True)
        self.assertEqual(0.0, port.output)
        port = client.get_port(label='Relay Control')
        self.assertEqual(1.0, port.output)
        port.control(False)
        port = client.get_port(label='Relay Control')
        self.assertEqual(0.0, port.output)


class TestClientRequests(unittest.TestCase):
    @mock.patch('requests.Session')
    def test_login_success(self, mock_session):
        session = mock_session.return_value
        session.post.return_value.status_code = 200
        session.post.return_value.url = '/manage'
        with mock.patch.object(client.MFiClient, '_login') as login:
            c = client.MFiClient('host', 'user', 'pass')
            login.assert_called_once_with()
        c._login()
        mock_session.assert_called_once_with()
        url = 'https://host:6443'
        session.get.assert_called_once_with(url, verify=False)
        data = {'username': 'user',
                'password': 'pass',
                'login': 'Login'}
        session.post.assert_called_once_with(url + '/login', data=data)

    @mock.patch('requests.Session')
    def test_login_fail(self, mock_session):
        session = mock_session.return_value
        session.post.return_value.status_code = 401
        session.post.return_value.url = '/manage'
        with mock.patch.object(client.MFiClient, '_login'):
            c = client.MFiClient('host', 'user', 'pass')
        self.assertRaises(client.FailedToLogin, c._login)

    def test_get_stat(self):
        with mock.patch.object(client.MFiClient, '_login'):
            c = client.MFiClient('host', 'user', 'pass')
        with mock.patch.object(c, '_session') as mock_session:
            mock_session.get.return_value.json.return_value = {'data': 'foo'}
            result = c._get_stat()
            mock_session.get.assert_called_once_with(
                'https://host:6443/api/v1.0/stat/device')
            self.assertEqual('foo', result)

    def test_get_sensors(self):
        with mock.patch.object(client.MFiClient, '_login'):
            c = client.MFiClient('host', 'user', 'pass')
        weirdo = {'json': json.dumps({'hello': 2})}
        with mock.patch.object(c, '_session') as mock_session:
            mock_session.post.return_value.json.return_value = {'data': 'foo'}
            result = c._get_sensors()
            mock_session.post.assert_called_once_with(
                'https://host:6443/api/v1.0/list/sensors',
                data=weirdo)
            self.assertEqual('foo', result)

    def test_control_device(self):
        with mock.patch.object(client.MFiClient, '_login'):
            c = client.MFiClient('host', 'user', 'pass')
        data = {
            'sId': 'ident',
            'mac': 'mac',
            'model': 'model',
            'port': 1,
            'cmd': 'mfi-output',
            'val': 1,
            'volt': 0,
        }
        data = {'json': json.dumps(data)}
        with mock.patch.object(c, '_session') as mock_session:
            with mock.patch.object(c, '_find_port') as mock_fp:
                mock_fp.return_value = {'mac': 'mac',
                                        'model': 'model',
                                        'port': '1'}
                mock_session.post.return_value.text = 'foo'
                result = c._control_port('ident', True)
                mock_session.post.assert_called_once_with(
                    'https://host:6443/api/v1.0/cmd/devmgr',
                    data=data)
                self.assertEqual('foo', result)
