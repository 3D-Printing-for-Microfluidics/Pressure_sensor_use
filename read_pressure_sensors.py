'''
    Finds Teensy 3.2 comport and polls data from serial input.
    Echoes serial input to a csv file. Assumes input structure of:

        <timestamp>:<adc0_value>:<adc1_value>

    Outputs:

        One csv file with the polled data.

    Usage

        python read_pressure_sensors.py
'''

import sys
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from teensy import Teensy

def show_figure(x, y):
    plt.xlabel('Time (us)')
    plt.ylabel('Pressure (counts)')
    plt.title('Uncalibrated Pressure Readings Gain={}, {} PSI'.format(gain, pressure))
    plt.grid(True)
    plt.plot(x, y)
    plt.tight_layout()
    test_name = 'test_{}_{}G_{}psi'.format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), gain, pressure)
    plt.savefig(test_name + '.png')
    plt.show()

def save_data(time, adc0, adc1,):
    test_name = 'test_{}_{}G_{}psi'.format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), gain, pressure)
    df = pd.DataFrame({
        'us'  : time,
        'adc0': adc0,
        'adc1': adc1
    })
    df.to_csv(test_name + '.csv')

if __name__ == '__main__':

    t = Teensy(verbose=False)
    t.connect()

    gain = 16
    pressure = sys.argv[1]
    points_to_acquire = 10000

    timestamps, data0, data1 = t.sample(points_to_acquire)
    show_figure(timestamps, data0)
    save_data(timestamps, data0, data1)
