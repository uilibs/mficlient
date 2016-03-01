Client for Ubiquiti's mFi system
================================

.. image:: https://travis-ci.org/kk7ds/mficlient.svg?branch=master
    :target: https://travis-ci.org/kk7ds/mficlient

The APIs in this library (and tool) should not be considered stable!

To install::

 $ pip install mficlient

To get started, set your connection information like this::

 $ export MFI="https://user:password@192.168.1.123:6443"

Then you can run the client, doing something like::

 $ mfi dump_sensors
                Model |                Label |        Tag  |      Value | Extra
 -------------------------------------------------------------------------------
           Output 12v |        Relay Control |     output  |          0 | 0.0
           Output 24v |                Relay |     output  |          0 | 0.0
     Ubiquiti mFi-THS |                 Temp | temperature |       14.3 | None
        Input Digital |          Garage Door |      input  |          1 | None
               Outlet |       Heater Control | active_pwr  |   5.810242 | 1.0
      Ubiquiti mFi-CS |              Furnace |       amps  |     1.0539 | None
      Ubiquiti mFi-CS |         Water Heater |       amps  |        0.0 | None

 $ mfi control_device --device 'Heater Control' --state on

Client API example::

 >>> c = mficlient.MFiClient('192.168.1.123', 'admin', 'password')
 >>> p = c.get_port(label='Water Heater Control')
 >>> p.model
 'Outlet'
 >>> p.value
 5.746462
 >>> p.tag
 'active_pwr'
 >>> p.data
 {'rpt_time': 1456258144771, 'mac': 'redacted', 'locked': False, 'label': 'Water Heater Control', 'wattHours': 8001.875, 'y': 222.18320610687024, 'map_id': 'redacted', 'output': 1.0, 'fovrotation': 0, 'active_pwr': 5.746462, 'pf': 0.678653, 'reported_val': 1.0, '_id': 'redacted', 'i_rms': 0.069931, 'fovradius': 10, 'v_rms': 121.082737, 'val_time': 1456258144000, 'port': '1', 'energy_sum': 8001.875, 'wattHoursBase': 0.0, 'tag': 'active_pwr', 'val': 5.746462, 'wh_rpt_time': 1456258144761, 'model': 'Outlet', 'x': 564.8839694656489, 'fovangle': 1.5707963267948966, 'output_val': 1.0}
  >>> p.control(False)
