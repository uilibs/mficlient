Client for Ubiquiti's mFi system
================================

The APIs in this library (and tool) should not be considered stable!

To install:

 $ pip install mficlient

To get started, set your connection information like this::

 $ export MFI="http://user:password@192.168.1.123:6443"

Then you can run the client, doing something like:

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
