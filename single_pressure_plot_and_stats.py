'''
    Calculate statistics and generate graphs for raw sensor data
    using a variety of window sizes. Generates one plot using each
    window size per data file input.

    Inputs:

        sys.argv[1] - directory containing raw data. Generated images also save here
        sys.argv[2] - name of the sensor being tested. Gets appended to generated file names
        sys.argv[3] - supply voltage for sensor. Gets appended to generated file names

    Outputs:

        One plot for each data point and window size
        Detailed statistics for each pressure point and window size

    Usage

        python single_pressure_plot_and_stats.py path_to_data_files/ 'name_of_sensor' 'supply_voltage'
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

def make_figure(x, y, filename, title='Figure'):
    plt.xlabel('Time (ms)')
    plt.ylabel('Adc Output (raw, uncalibrated)')
    plt.ylim(-25000, 3000)
    plt.title(title)
    plt.grid(True)
    # for i in y:
    #     plt.plot(x, i, label=pressure)
    plt.plot(x, y)
    plt.tight_layout()
    filename = filename.replace('.csv', '') + '_' + title.replace(' ', '_').lower() + '.png'
    print("Saving ", filename)
    plt.savefig(filename)
    plt.clf()
    # plt.show()

def natural_sort(s):
    _natural_sort_regex = re.compile(r'([0-9]+)')
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_natural_sort_regex, s)]

# build list of files to analyze
file_list = glob.glob(sys.argv[1]+"/*.csv")
file_list.sort(key=natural_sort)

# dataframe to hold results
df = pd.DataFrame(columns=["Data Set Name", "Pressure", "# Samples", "Min", "Max", "Average", "SDev"])

# parse and do calculations for each file
for f in file_list:
    try:
        gain = int(re.findall(r'(\d+)G', f)[0])                 # parse out gain from filename
        pressure = float(re.findall(r'_(\d+\.\d+)psi', f)[0])   # parse out gain from filename
    except IndexError:
        continue            # skip analysis for files that don't have gain in the name

    idx, ts, adc0, adc1 = parse_and_sanitize_input_data(f)   # parse data from file

    # calculate stats we care about for this data set
    data = [f.split("\\")[-1], pressure, len(adc0), min(adc0), max(adc0), statistics.mean(adc0), statistics.stdev(adc0)]
    df = df.append(pd.Series(data, index=df.columns), ignore_index=True)

    # # try different averages and make figures
    for window_size in [1, 5, 10, 50, 100, 500]:
        averaged_data = rolling_average(adc0, window_size)
        make_figure(idx[window_size-1:], averaged_data, f, "Pressure={} psi Gain={} Window size={}".format(pressure, gain, window_size))

print(df)
df.to_csv(sys.argv[1] + "/calibration_data.csv")
