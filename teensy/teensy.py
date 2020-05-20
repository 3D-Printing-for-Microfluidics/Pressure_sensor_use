'''
    Finds Teensy 3.2 comport and polls data from serial input.
    Echoes serial input to a csv file. Assumes input structure of:

        <timestamp>:<adc0_value>:<adc1_value>

    Outputs:

        One csv file with the polled data.

    Usage

        python read_pressure_sensors.py
'''

import atexit
import serial
import serial.serialutil
import serial.tools.list_ports

def findUsbPort(hwid):
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if hwid.upper() in p.hwid:
            print("Found '{}' at '{}'".format(p.hwid, p.device))
            return p.device
    return None                 # hwid not found

class Teensy():

    def __init__(self, hwid='16c0:0483', verbose=True):
        self.serial_handle = serial.Serial(baudrate=115200, timeout=1)
        self.serial_handle.hwid = hwid
        self.serial_handle.port = None                # start with no port
        self.verbose = verbose
        atexit.register(self.serial_handle.close)

    def connect(self):
        self.serial_handle.port = findUsbPort(self.serial_handle.hwid)
        if self.serial_handle.port is None:
            raise ValueError('Teensy not found')
        if self.serial_handle.is_open:
            self.serial_handle.close()
        self.serial_handle.open()
        self.serial_handle.flushInput()
        self.serial_handle.flushOutput()
        print("Connected to", self.serial_handle.port)

    def send(self, cmd):
        if self.verbose: print('Sent: ' + cmd)
        self.serial_handle.write(bytes(cmd + '\n', encoding='ascii'))
        response = self.receive()
        # if self.verbose: print("Response: ", response)
        return response                                 # return the response to the command

    def receive(self):
        response = b''
        response += self.serial_handle.readline()       # wait for the first line to fill in the rx buffer
        return response.decode().rstrip()               # return decoded byte response (as string) without traililng newline

    def read_adcs(self):
        data = self.receive().split(':')
        if len(data) == 3:
            print(data[0], data[1], data[2])
            t0, v0, v1 = None, None, None
            try:                        # attempt type cast
                t0 = float(data[0])
                v0 = float(data[1])
                v1 = float(data[2])
            except ValueError:
                pass                # don't use anything if data was bad
        return t0, v0, v1

    def sample(self, num_samples, period_us=1000):
        times, adc0, adc1 = [], [], []
        num_datapoints = 0
        self.send("s")                         # stop the internal timer
        self.serial_handle.flushInput()        # flush serial input
        self.serial_handle.flushOutput()       # flush serial input
        self.send("s {}".format(period_us))    # set sampling period and begin sampling
        while num_datapoints < num_samples + 50:    # take 50 extra samples to get rid of
            t0, v0, v1 = self.read_adcs()
            if t0 is not None:                      # ignore bad datapoints
                times.append(t0)
                adc0.append(v0)
                adc1.append(v1)
                num_datapoints += 1
            if num_datapoints >= num_samples + 50:
                break
        self.send("s") # stop the data collection
        return times[50:], adc0[50:], adc1[50:]
