import json

from mficlient import client, fake_data


class FakeResponse:
    def __init__(self, code, data):
        self.status_code = code
        self._data = data

    def json(self):
        return {"data": self._data}

    @property
    def text(self):
        return self._data


class FakeSession:
    def __init__(self):
        self._status = json.loads(fake_data.FAKE_STATUS)
        self._sensors = json.loads(fake_data.FAKE_SENSORS)

    def get(self, url, headers=None, verify=True):
        if url.endswith("stat/device"):
            return FakeResponse(200, self._status)
        elif url.endswith("list/sensors"):
            return FakeResponse(200, self._sensors)
        else:
            raise Exception("Unsupported fake path %s" % url)

    def _do_device(self, data):
        cmd = json.loads(data["json"])
        updates = dict(cmd)
        ident = updates.pop("sId")
        for sensor in self._sensors:
            if sensor["_id"] == ident:
                sensor.update(updates)
            sensor["output"] = float(sensor["val"] > 0)
        return FakeResponse(200, self._sensors)

    def post(self, url, data=None, headers=None, verify=True):
        if url.endswith("list/sensors"):
            return FakeResponse(200, self._sensors)
        elif url.endswith("cmd/devmgr"):
            return self._do_device(data)


class FakeMFiClient(client.MFiClient):
    def __init__(self, *args, **kwargs):
        if not args:
            args = ("fakehost", "fakeuser", "fakepass")
        super().__init__(*args, **kwargs)
        self._session = FakeSession()

    def _login(self):
        pass
