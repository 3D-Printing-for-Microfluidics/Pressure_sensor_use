'''
    Plots data to an animated graph. Current implementation gets unstable with
    large data sets. At 1 ms per sample, it will run for about 20 seconds.
'''

import atexit
from datetime import datetime

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
        # while self.serial_handle.in_waiting:            # while there is more data in the rx buffer
        #     response += self.serial_handle.readline()   # read next line from rx buffer
        return response.decode().rstrip()               # return decoded byte response (as string) without traililng newline

if __name__ == '__main__':
    t = Teensy(verbose=True)
    t.connect()

    import matplotlib.pyplot as plt

    time = []
    data = []
    cnt = 0

    voltage = 10.25
    psi = 0

    plt.xlabel('Time (ms)')
    plt.ylabel('Voltage (V)')
    plt.title("Uncalibrated Pressure Readings {} V {} PSI".format(voltage, psi))
    plt.grid(True)

    while True:
        try:
            time.append(datetime.now())
            result = [i.split(':') for i in t.receive().splitlines()]   # result[0] is ADC_0, result[1] is ADC_1

            val = float(result[0][2])   # value from ADC_0
            data.append(val)

            cnt += 1

            if cnt == 3:
                plt.tight_layout()

            plt.plot(time, data, 'b')
            plt.pause(0.0001)
            if cnt == 200:
                plt.savefig("test_{}V_{}psi.png".format(voltage, psi))

                exit()

        except KeyboardInterrupt:
            exit()
