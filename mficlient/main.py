import argparse
import json
import os
import pprint
import time
from datetime import datetime

import requests

from mficlient import client
from mficlient.client import TIME_FORMAT


class Application(object):
    def main(self):
        try:
            requests.packages.urllib3.disable_warnings()
        except:  # noqa: E722
            pass
        commands = [x[4:] for x in dir(self) if x.startswith("cmd")]
        command_list = os.linesep + os.linesep.join(commands)

        parser = argparse.ArgumentParser()
        parser.add_argument("command", help="One of: %s" % command_list)
        parser.add_argument("--device", help="Specific device")
        parser.add_argument("--property", help="Show only this property of a device")
        parser.add_argument("--state", help="State to set (on or off)")
        parser.add_argument(
            "--every", type=int, default=0, help="Repeat (interval in seconds)"
        )
        parser.add_argument(
            "--since",
            type=int,
            default=60,
            metavar="SECS",
            help="Show data since SECS seconds ago",
        )
        parser.add_argument(
            "--column-headers",
            default=False,
            action="store_true",
            help="Show CSV column headers",
        )
        parser.add_argument(
            "--json",
            default=False,
            action="store_true",
            help="Output raw JSON for the raw_ commands",
        )
        parser.add_argument(
            "--noverify",
            default=False,
            action="store_true",
            help="Do not verify server SSL certificate",
        )
        args = parser.parse_args()

        if not hasattr(self, "cmd_%s" % args.command):
            print("No such command `%s'" % args.command)
            return 1

        host, port, user, _pass, path, tls = client.get_auth_from_env()
        self._client = client.MFiClient(
            host, user, _pass, port=port, use_tls=tls, verify=not args.noverify
        )

        while True:
            getattr(self, "cmd_%s" % args.command)(args)
            if not args.every:
                break
            time.sleep(args.every)

    def cmd_dump_sensors(self, options):
        devices = self._client.get_devices()

        fmt = "%20s | %20s | %15s | %10s | %s"
        print(fmt % ("Model", "Label", "Tag", "Value", "Extra"))
        print("-" * 78)
        for device in devices:
            for port in device.ports.values():
                print(fmt % (port.model, port.label, port.tag, port.value, port.output))

    def cmd_raw_sensors(self, options):
        data = self._client.get_raw_sensors()
        if options.device:
            data = [x for x in data if x["label"] == options.device]
        if options.json:
            print(json.dumps(data))
        else:
            pprint.pprint(data)

    def cmd_raw_status(self, options):
        data = self._client.get_raw_status()
        if options.json:
            print(json.dumps(data))
        else:
            pprint.pprint(data)

    def cmd_control_device(self, options):
        if not options.device:
            print("Must specify a device")
            return
        if not options.state:
            print("Must specify a state")
            return
        port = self._client.get_port(label=options.device)
        port.control(options.state == "on")

    def cmd_get_data(self, options):
        if not options.device:
            print("Must specify a device")
            return

        devices = self._client.get_devices()
        port = None
        for dev in devices:
            for port in dev.ports.values():
                if port.label == options.device:
                    break
        if port is None:
            print("No such port %s" % options.device)
            return

        headers = list(port.data.keys())
        if options.property:
            if options.property not in headers:
                print("Port has no property `%s`" % options.property)
                return
            headers = [options.property]

        data = [str(port.data[key]) for key in headers]

        if options.column_headers:
            print(",".join(headers))
        print(",".join(data))

    def cmd_sensors_csv(self, options):
        if not options.device:
            print("Must specify a device")
            return
        sensors = self._client.get_raw_sensors()
        keys = [
            "active_pwr",
            "energy_sum",
            "i_rms",
            "v_rms",
            "label",
            "model",
            "output",
            "output_val",
            "pf",
            "port",
            "tag",
            "val",
            "wattHours",
            "wattHoursBase",
        ]
        the_sensor = None
        for sensor in sensors:
            if sensor["label"] == options.device:
                the_sensor = sensor
                break

        if not the_sensor:
            print("No such device `%s'" % options.device)
            return

        rpt_time = datetime.fromtimestamp(sensor["rpt_time"] / 1000)
        try:
            wh_rpt_time = datetime.fromtimestamp(sensor["wh_rpt_time"] / 1000)
        except KeyError:
            wh_rpt_time = ""

        vals = [str(sensor.get(k, "")) for k in keys]
        vals.insert(0, rpt_time.strftime(TIME_FORMAT))
        vals.append(wh_rpt_time and wh_rpt_time.strftime(TIME_FORMAT) or "")
        keys.insert(0, "time")
        keys.append("wh_rpt_time")

        if options.column_headers:
            print(",".join(keys))

        print(",".join(vals))
