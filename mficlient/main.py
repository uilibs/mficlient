import argparse
import os
import pprint

from mficlient import client


class Application(object):
    def main(self):
        commands = [x[4:] for x in dir(self) if x.startswith('cmd')]
        command_list = os.linesep + os.linesep.join(commands)

        parser = argparse.ArgumentParser()
        parser.add_argument('command',
                            help='One of: %s' % command_list)
        parser.add_argument('--device',
                            help='Specific device')
        parser.add_argument('--state',
                            help='State to set (on or off)')
        parser.add_argument('--every', type=int, default=0,
                            help='Repeat (interval in seconds)')
        parser.add_argument('--since', type=int, default=60,
                            metavar='SECS',
                            help='Show data since SECS seconds ago')
        parser.add_argument('--column-headers', default=False,
                            action='store_true',
                            help='Show CSV column headers')
        args = parser.parse_args()

        if not hasattr(self, 'cmd_%s' % args.command):
            print('No such command `%s\'' % args.command)
            return 1

        host, port, user, _pass, path, = client.get_auth_from_env()
        self._client = client.MFiClient(host, user, _pass, port=port)

        while True:
            getattr(self, 'cmd_%s' % args.command)(args)
            if not args.every:
                break
            time.sleep(args.every)

    def cmd_dump_sensors(self, options):
        data = self._client.get_sensors()

        fmt = '%20s | %20s | %10s | %10s | %s'
        print(fmt % ('Model', 'Label', 'Tag', 'Value', 'Extra'))
        print('-' * 78)
        for sensor in data:
            print(fmt % (sensor['model'], sensor['label'],
                         sensor.get('tag'), sensor.get('val'),
                         sensor.get('output')))

    def cmd_raw_sensors(self, options):
        data = self._client.get_sensors()
        pprint.pprint(data)

    def cmd_raw_status(self, options):
        data = self._client.get_stat()
        pprint.pprint(data)

    def cmd_raw_device(self, options):
        if not options.device:
            print('Must specify a device')
            return
        try:
            data = self._client.get_device(options.device)
        except DeviceNotFound as e:
            print('Error: %s' % e)
            return
        pprint.pprint(data)

    def cmd_control_device(self, options):
        if not options.device:
            print('Must specify a device')
            return
        if not options.state:
            print('Must specify a state')
            return
        try:
            self._client.control_device(options.device,
                                        options.state == 'on')
        except DeviceNotFound as e:
            print('Error: %s' % e)
            return

    def cmd_get_data(self, options):
        if not options.device:
            print('Must specify a device')
            return
        try:
            data = self._client.get_device_data(options.device,
                                                options.since)
        except DeviceNotFound as e:
            print('Error: %s' % e)
            return

        if options.column_headers:
            print('time,min,max')

        for sample in data:
            dt = datetime.datetime.fromtimestamp(sample['time'] / 1000)
            print('%s,%s,%s' % (dt.strftime(TIME_FORMAT),
                                sample['min'],
                                sample['max']))

    def cmd_sensors_csv(self, options):
        if not options.device:
            print('Must specify a device')
            return
        sensors = self._client.get_sensors()
        keys = ['active_pwr', 'energy_sum', 'i_rms', 'v_rms',
                'label', 'model', 'output', 'output_val', 'pf',
                'port', 'tag', 'val', 'wattHours', 'wattHoursBase']
        the_sensor = None
        for sensor in sensors:
            if sensor['label'] == options.device:
                the_sensor = sensor
                break

        if not the_sensor:
            print('No such device `%s\'' % options.device)
            return

        rpt_time = datetime.datetime.fromtimestamp(
            sensor['rpt_time'] / 1000)
        try:
            wh_rpt_time = datetime.datetime.fromtimestamp(
                sensor['wh_rpt_time'] / 1000)
        except KeyError:
            wh_rpt_time = ''

        vals = [str(sensor.get(k, '')) for k in keys]
        vals.insert(0, rpt_time.strftime(TIME_FORMAT))
        vals.append(wh_rpt_time and wh_rpt_time.strftime(TIME_FORMAT) or '')
        keys.insert(0, 'time')
        keys.append('wh_rpt_time')

        if options.column_headers:
            print(','.join(keys))

        print(','.join(vals))
