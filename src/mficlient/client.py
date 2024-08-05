import functools
import json
import os
import time

import requests

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class FailedToLogin(Exception):
    pass


class DeviceNotFound(Exception):
    pass


class RequestFailed(Exception):
    pass


class Device:
    def __init__(self, client, ident):
        self._client = client
        self.ident = ident
        self._devinfo = {}
        self._ports = {}

    def refresh(self, info=None):
        if info is None:
            info = self._client._find_device(ident=self.ident)
        self._devinfo = info

    def set_port(self, port):
        self._ports[port.ident] = port

    @property
    def ports(self):
        return self._ports

    @property
    def data(self):
        return self._devinfo


class Port:
    def __init__(self, client, ident):
        self._client = client
        self.ident = ident
        self._portinfo = {}

    def refresh(self, info=None):
        if info is None:
            sensors = self._client._get_sensors()
            info = self._client._find_sensor(sensors, self.ident)
        self._portinfo.update(info)

    def __repr__(self):
        try:
            data = "%s=%s" % (self.tag, self.value)
        except ValueError:
            data = "?"
        return "<Port %s %s>" % (self.ident, data)

    @property
    def value(self):
        if "tag" not in self._portinfo:
            raise ValueError("Port has no value")
        return self._portinfo.get(self.tag)

    @property
    def tag(self):
        if "tag" not in self._portinfo:
            raise ValueError("Port is not initialized")
        return self._portinfo["tag"]

    @property
    def data(self):
        return self._portinfo

    @property
    def label(self):
        return self._portinfo["label"]

    @property
    def model(self):
        return self._portinfo["model"]

    @property
    def output(self):
        return self._portinfo.get("output")

    def control(self, state):
        self._client._control_port(self.ident, state)


def retries_login(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        for i in (0, 1):
            try:
                return fn(self, *args, **kwargs)
            except RequestFailed:
                if i == 0:
                    self._login()
                else:
                    # Make sure we raise the original exception
                    # if we retried login already and still explode
                    raise

    return wrapper


class MFiClient:
    def __init__(self, host, username, password, port=None, use_tls=True, verify=True):
        self._host = host
        self._port = port
        self._user = username
        self._pass = password
        self._stat_cache = None
        self._cookie = None
        self._session = requests.Session()
        self._verify = verify
        if use_tls:
            port = port or 6443
            self._baseurl = "https://%s:%i" % (host, port)
        else:
            port = port or 6080
            self._baseurl = "http://%s:%i" % (host, port)

        self._login()

    def _login(self):
        response = self._session.get(self._baseurl, verify=self._verify)

        data = {"username": self._user, "password": self._pass, "login": "Login"}

        response = self._session.post(
            "%s/login" % self._baseurl, data=data, verify=self._verify
        )
        if response.status_code == 200 and response.url.endswith("/manage"):
            return

        raise FailedToLogin("Server rejected login")

    @retries_login
    def _get_stat(self):
        response = self._session.get(
            "%s/api/v1.0/stat/device" % self._baseurl, verify=self._verify
        )
        if response.status_code == 200:
            return response.json()["data"]
        raise RequestFailed()

    @retries_login
    def _get_sensors(self):
        data = {"json": json.dumps({"hello": 2})}
        response = self._session.post(
            "%s/api/v1.0/list/sensors" % self._baseurl, data=data, verify=self._verify
        )
        if response.status_code == 200:
            return response.json()["data"]
        raise RequestFailed()

    get_raw_sensors = _get_sensors
    get_raw_status = _get_stat

    @staticmethod
    def _find_sensor(sensors, ident):
        for sensor in sensors:
            if sensor["_id"] == ident:
                return sensor
        raise DeviceNotFound("No sensor %s" % ident)

    def get_devices(self):
        stat = self._get_stat()
        sensors = self._get_sensors()

        devices = []
        for devinfo in stat:
            device = Device(self, devinfo["_id"])
            for portinfo in devinfo["port_cfg"]:
                if portinfo["_id"] == "NONE":
                    continue
                sensorinfo = self._find_sensor(sensors, portinfo["_id"])

                port = Port(self, portinfo["_id"])
                port.refresh(portinfo)
                port.refresh(sensorinfo)
                device.set_port(port)
            devices.append(device)
        return devices

    def get_port(self, ident=None, label=None):
        for device in self.get_devices():
            for port in device.ports.values():
                if port.label == label or port.ident == ident:
                    return port
        return None

    def get_stat(self):
        if not self._stat_cache:
            self._stat_cache = self._get_stat()
        return self._stat_cache

    @retries_login
    def _control_port(self, ident, state, voltage=0):
        the_port = self._find_port(ident=ident)

        voltages = {
            "Output 5v": 5,
            "Output 12v": 12,
            "Output 24v": 24,
        }
        voltage = state and voltages.get(the_port["model"], 0) or 0

        data = {
            "sId": ident,
            "mac": the_port["mac"],
            "model": the_port["model"],
            "port": int(the_port["port"]),
            "cmd": "mfi-output",
            "val": int(state),
            "volt": voltage,
        }
        data = {"json": json.dumps(data)}
        response = self._session.post(
            "%s/api/v1.0/cmd/devmgr" % self._baseurl, data=data, verify=self._verify
        )
        if response.status_code == 200:
            return response.text
        raise RequestFailed()

    def _find_port(self, ident=None, device_name=None):
        devices = self.get_stat()

        for dev in devices:
            for port in dev["port_cfg"]:
                if port["_id"] == ident:
                    return port
                if port["label"] == device_name:
                    return port
        raise DeviceNotFound("No such device")

    def get_device_data(self, device, since=60):
        # NOTE: This is broken
        port = self._find_device(device)
        sensor = self._find_sensor(device)

        start = time.time() - since
        end = time.time()
        data = {
            "fmt": "json",
            "ids": port["_id"],
            "tags": sensor["tag"],
            "indices": "1,2,3,4",
            "func": "trend",
            "collection": "null",
            "startTime": int(start) * 1000,
            "endTime": int(end) * 1000,
        }
        response = self._session.get(
            "%s/api/v1.0/data/m2mgeneric_by_id" % self._baseurl,
            params=data,
            verify=self._verify,
        )
        return response.json()["data"][0]["%s.0" % sensor["tag"]]


def get_auth_from_env():
    """
    Attempt to get mFi connection information from the environment.

    Supports either a combined variable called MFI formatted like:

        MFI="http://user:pass@192.168.1.1:6080/

    or individual ones like:

        MFI_HOST=192.168.1.1
        MFI_PORT=6080
        MFI_USER=foo
        MFI_PASS=pass

    :returns: A tuple like (host, port, user, pass, path)
    """
    combined = os.getenv("MFI")
    if combined:
        # http://user:pass@192.168.1.1:7080/
        result = urlparse.urlparse(combined)
        netloc = result.netloc
        if "@" in netloc:
            creds, netloc = netloc.split("@", 1)
            user, _pass = creds.split(":", 1)
        else:
            user = "mfiadmin"
            _pass = "password"  # noqa: S105
        if ":" in netloc:
            host, port = netloc.split(":", 1)
            port = int(port)
        else:
            host = netloc
            port = 6080
        path = result.path
        tls = combined.startswith("https://")
    else:
        host = os.getenv("MFI_HOST")
        port = int(os.getenv("MFI_PORT", 7080))
        user = os.getenv("MFI_USER")
        _pass = os.getenv("MFI_PASS")
        path = "/"
        tls = False
    return host, port, user, _pass, path, tls


def envclient():
    host, port, user, _pass, path = get_auth_from_env()
    return MFiClient(host, user, _pass, port=port)
