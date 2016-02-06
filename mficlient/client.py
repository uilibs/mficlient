import argparse
import datetime
import json
import os
import pprint
import urllib
import requests
import sys
import time

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class FailedToLogin(Exception):
    pass


class DeviceNotFound(Exception):
    pass


class MFiClient(object):
    def __init__(self, host, username, password, port=6443):
        self._host = host
        self._port = port
        self._user = username
        self._pass = password
        self._stat_cache = None
        self._cookie = None
        self._session = requests.Session()
        self._baseurl = 'https://%s:%i' % (host, port)
        self._login()

    def _login(self):
        response = self._session.get(self._baseurl, verify=False)

        data = {'username': self._user,
                'password': self._pass,
                'login': 'Login'}

        response = self._session.post('%s/login' % self._baseurl,
                                      data=data)
        if response.status_code == 200 and response.url.endswith('/manage'):
            return

        raise FailedToLogin('Server rejected login')

    def _get_stat(self):
        response = self._session.get('%s/api/v1.0/stat/device' % self._baseurl)
        return response.json()['data']

    def get_stat(self):
        if not self._stat_cache:
            self._stat_cache = self._get_stat()
        return self._stat_cache

    def control_device(self, device_name, state):
        the_port = self._find_device(device_name)

        if (the_port['model'].startswith('Output') and
                '12' in the_port['model']):
            voltage = state and 12 or 0

        data = {
            'sId': the_port['_id'],
            'mac': the_port['mac'],
            'model': the_port['model'],
            'port': int(the_port['port']),
            'cmd': 'mfi-output',
            'val': int(state),
            'volt': voltage,
        }
        data = {'json': json.dumps(data)}
        response = self._session.post('%s/api/v1.0/cmd/devmgr' % self._baseurl,
                                      data=data)
        return response.text

    def _find_device(self, device_name):
        devices = self.get_stat()

        for dev in devices:
            for port in dev['port_cfg']:
                if port['label'] == device_name:
                    return port
        raise DeviceNotFound('No such device `%s\'' % device_name)

    def _find_sensor(self, device_name):
        sensors = self.get_sensors()

        for sensor in sensors:
            if sensor['label'] == device_name:
                return sensor
        raise DeviceNotFound('No such device `%s\'' % device_name)

    def get_device(self, device):
        return self._find_device(device)

    def get_device_data(self, device, since=60):
        port = self._find_device(device)
        sensor = self._find_sensor(device)

        start = time.time() - since
        end = time.time()
        data = {
            'fmt': 'json',
            'ids': port['_id'],
            'tags': sensor['tag'],
            'indices': '1,2,3,4',
            'func': 'trend',
            'collection': 'null',
            'startTime': int(start) * 1000,
            'endTime': int(end) * 1000,
        }
        response = self._session.get(
            '%s/api/v1.0/data/m2mgeneric_by_id' % self._baseurl,
            params=data)
        return response.json()['data'][0]['%s.0' % sensor['tag']]

    def get_sensors(self):
        data = {
            'json': json.dumps({'hello': 2}),
        }
        response = self._session.post(
            '%s/api/v1.0/list/sensors' % self._baseurl, data=data)
        return response.json()['data']


def get_auth_from_env():
    """Attempt to get mFi connection information from the environment.

    Supports either a combined variable called MFI formatted like:

        MFI="http://user:pass@192.168.1.1:7080/

    or individual ones like:

        MFI_HOST=192.168.1.1
        MFI_PORT=6080
        MFI_USER=foo
        MFI_PASS=pass

    :returns: A tuple like (host, port, user, pass, path)
    """

    combined = os.getenv('MFI')
    if combined:
        # http://user:pass@192.168.1.1:7080/
        result = urlparse.urlparse(combined)
        netloc = result.netloc
        if '@' in netloc:
            creds, netloc = netloc.split('@', 1)
            user, _pass = creds.split(':', 1)
        else:
            user = 'mfiadmin'
            _pass = 'password'
        if ':' in netloc:
            host, port = netloc.split(':', 1)
            port = int(port)
        else:
            host = netloc
            port = 6080
        path = result.path
    else:
        host = os.getenv('MFI_HOST')
        port = int(os.getenv('MFI_PORT', 7080))
        user = os.getenv('MFI_USER')
        _pass = os.getenv('MFI_PASS')
        path = '/'
    return host, port, user, _pass, path
