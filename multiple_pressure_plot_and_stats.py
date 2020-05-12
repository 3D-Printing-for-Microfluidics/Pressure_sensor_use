'''
    Calculate statistics and generate graphs for raw sensor data using a
    variety of window sizes. Assumes a csv file for each pressure data
    point and overlays all pressure readings on a single plot.

    Inputs:

        sys.argv[1] - directory containing raw data. Generated images
                      also save here
        sys.argv[2] - name of the sensor being tested. Gets appended to
                      generated file names
        sys.argv[3] - supply voltage for sensor. Gets appended to
                      generated file names

    Outputs:

        One plot for each window size, containing all data for each
        pressure point and detailed statistics for each pressure point
        and window size combination.

    Usage

        python multiple_pressure_plot_and_stats.py path_to_data_files/ 'name_of_sensor' 'supply_voltage'
'''

import sys
import csv
import glob
import re
import statistics

import pandas as pd
import matplotlib.pyplot as plt


def parse_and_sanitize_input_data(filename):
    data = []
    with open(filename) as csvfile:
        data = list(csv.reader(csvfile))
    col0, col1, col2, col3 = [], [], [], []
    for row in data:
        try:
            float(row[0]), float(row[1]), float(row[2]), float(row[3])
        except ValueError:
            continue        # skip rows that have non numerical data
        col0.append(float(row[0]))
        col1.append(float(row[1]))
        col2.append(float(row[2]))
        col3.append(float(row[3]))
    return col0, col1, col2, col3

def rolling_average(data, window_size):
    rolling_sum, result = [0], []
    for i, x in enumerate(data, 1):
        rolling_sum.append(rolling_sum[i-1] + x)
        if i >= window_size:
            curr_average = (rolling_sum[i] - rolling_sum[i-window_size])/window_size
            result.append(curr_average)
    return result

def make_figure(data, window_size, filename, title='Figure'):
    plt.xlabel('Time (ms)')
    plt.ylabel('ADC Output (raw, uncalibrated)')
    plt.ylim(-25000, 5000)
    plt.xlim(0, 13000)
    plt.title(title)
    plt.grid(True)

    for i, _ in enumerate(data):
        pressure = data[i]['pressure']
        idx = data[i]['time']
        averaged_data = data[i]['averaged']
        plt.plot(idx[window_size-1:], averaged_data, label=pressure)

    plt.tight_layout()
    # filename = filename.replace('.csv', '') + '_' + title.replace(' ', '_').lower() + '.png'
    print('Saving ', filename)
    plt.legend(loc='upper right', title='Pressure (PSI)')
    # plt.show()
    plt.savefig(filename)
    plt.clf()

def natural_sort(s):
    _natural_sort_regex = re.compile(r'([0-9]+)')
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_natural_sort_regex, s)]

# structure to hold all data
raw_data = []
raw_data.append([]) # adc0
raw_data.append([]) # adc1

# build list of files to analyze
file_list = glob.glob(sys.argv[1]+'/*.csv')
file_list.sort(key=natural_sort)

# parse all csv data files
for f in file_list:
    try:
        gain = int(re.findall(r'(\d+)G', f)[0])                 # parse out gain from filename
        pressure = float(re.findall(r'_(\d+\.\d+)psi', f)[0])   # parse out gain from filename
    except IndexError:
        continue            # skip analysis for files that don't have gain in the name

    idx, ts, adc0, adc1 = parse_and_sanitize_input_data(f)      # parse data from file
    raw_data[0].append({'datafile': f, 'pressure': pressure, 'time': idx, 'raw': adc0})
    raw_data[1].append({'datafile': f, 'pressure': pressure, 'time': idx, 'raw': adc1})

sensor = sys.argv[2]
voltage = sys.argv[3]

# calculate stats and make plots for each adc
for adc, _ in enumerate(raw_data):
    df = pd.DataFrame(columns=['Data Set Name', 'Pressure', '# Samples', 'Window', 'Min', 'Max', 'Average', 'SDev'])

    # try different averages
    for window_size in [1, 5, 10, 50, 100, 500]:

        # for each pressure measurement
        for i, _ in enumerate(raw_data[adc]):
            pressure = raw_data[adc][i]['pressure']
            raw = raw_data[adc][i]['raw']
            idx = raw_data[adc][i]['time']
            f = raw_data[adc][i]['datafile']

            # calculate stats we care about for this data set
            raw_data[adc][i]['averaged'] = rolling_average(raw, window_size)
            raw = raw_data[adc][i]['averaged']
            stats = [f.split('\\')[-1], float(pressure), len(raw), window_size, min(raw), max(raw), statistics.mean(raw), statistics.stdev(raw)]
            df = df.append(pd.Series(stats, index=df.columns), ignore_index=True)

        # overlay each pressure reading on one plot
        title_text = 'Sensor {}, ADC {}, {}V supply, Gain={}, Window size={}'.format(sensor, adc, voltage, gain, window_size)
        figure_filename = sys.argv[1] + 'sensor_{}_{}V_adc{}_{}_averages.png'.format(sensor, voltage, adc, window_size)
        make_figure(raw_data[adc], window_size, figure_filename, title_text)

    df = df.sort_values(['Pressure', 'Window'])
    print(df.round(2))
    df.to_csv(sys.argv[1] + '/calibration_data_sensor_{}_adc{}_{}V.csv'.format(sensor, adc, voltage))
