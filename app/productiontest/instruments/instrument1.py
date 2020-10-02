import mido
import time
import serial
from serial.tools import list_ports
from app.productiontest.instruments.instrument_base import InstrumentBase


class Instrument1(InstrumentBase):

    def __init__(self):
        self.name = 'INSTRUMENT1'
        self.manufacturer = 'ARTIPHON'
        self.sysex_header = [0, 2, 3, 0, 0, 0, 0, 0]
        self.attached = self._is_connected()

        self.serial_port_name = None
        self.serial_port_conn = None

    def _json_to_sysex_data(self, json_string):
        return self.sysex_header + [ord(letter) for letter in json_string]

    @staticmethod
    def _sysex_data_to_json(sysex_list):
        return ''.join([chr(nm) for nm in sysex_list])

    def _is_connected(self):
        midi_devices = mido.get_input_names()
        if self.name in midi_devices:
            return True
        else:
            return False

    def set_development_mode(self, val):

        bool_val = 'true' if val else 'false'
        json = '{{"msgid": 1, "cmd": "set", "data": {{"development": {{"cdc": {0},  "terminal_octave_raw": {0}, ' \
               '"terminal_fingerboard_raw": {0}, "terminal_bridgeboard_raw": {0} }} }} }}'.format(bool_val)
        message = mido.Message('sysex', data=self._json_to_sysex_data(json))

        outport = mido.open_output(self.name)
        outport.send(message)

        if val:
            # if turning on serial port reading
            # wait for device to appear as serial device
            time.sleep(5)
            ports = list(list_ports.comports())
            port = [p for p in ports if self.name == p.product]

            self.serial_port_name = port[0].device
            self.serial_port_conn = serial.Serial(self.serial_port_name, timeout=1)

            # must write to serial port in order to start reporting
            self.serial_port_conn.write(b'GoMoFo')

    def read_sensor(self, sensor_name):

        all_sensor_vals = self.read_all(split_sensor_name='OCTAVE_RAW_9C')

        print(all_sensor_vals)

        if sensor_name in all_sensor_vals:

            reading = all_sensor_vals.split(sensor_name + ':')[1].split('\r\n')[0]

            if len(reading) == 2:

                val = int(reading, 16)

                return val

        return 0

    def read_all(self, split_sensor_name='OCTAVE_RAW_9C'):

        port_reading = self.serial_port_conn.read(8192).decode('utf-8')

        if port_reading and split_sensor_name in port_reading:

            all_sensor_vals = split_sensor_name + port_reading.split(split_sensor_name)[1]

            return all_sensor_vals

        else:
            return ''

    def stream(self):
        CUTOFF = 10

        while True:

            all_vals = self.read_all()
            all_vals = all_vals.split('\r\n')

            all_vals_dict = {}
            for v in all_vals:
                k = v.split(':')[0]
                v = v.split(':')[-1]
                if v:
                    int_val = int(v, 16)
                    if int_val > CUTOFF:
                        all_vals_dict[k] = int_val

            for k in sorted(all_vals_dict.keys()):
                print(k, ':', all_vals_dict[k])



