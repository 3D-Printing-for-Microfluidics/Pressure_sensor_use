import sys
import os
import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# make float printing a little prettier
np.set_printoptions(formatter={'float': "{0:0.3e}".format})

# build list of files to analyze
file_list = Path(sys.argv[1]).rglob('*calibration_data*/*calibration_data*.csv')
degree = int(sys.argv[2])

df = pd.DataFrame(columns=['Data Set Name', 'Sensor', 'ADC', 'Degree', 'C[0]', 'C[1]', 'C[2]', 'C[3]'])

# parse all csv data files
for f in file_list:
    try:
        sensor = re.findall(r'sensor_(.)_', f.name)[0]  # parse out sensor name from filename
        adc = re.findall(r'adc(\d)', f.name)[0]         # parse out adc from filename
    except IndexError:
        continue

    # read data file
    data = pd.read_csv(f, index_col=[0])
    pressure = data.loc[data['Window'] == 1]['Pressure']
    avg_counts = data.loc[data['Window'] == 1]['Average']

    # calculate fit polynomial
    fit_x = np.linspace(min(avg_counts), max(avg_counts), num=1000)
    fit_coeffs = np.polyfit(avg_counts, pressure, deg=degree)
    fit_polynomial = [np.polyval(fit_coeffs, i) for i in fit_x]

    # draw plot
    base_name = 'calibration_data_sensor_{}_adc{}_10V_degree_{}'.format(sensor, adc, degree)
    plot_title = base_name.replace('_', ' ')
    filename = os.path.join(f.parent, base_name)
    plt.xlabel('ADC Output (counts)')
    plt.ylabel('Pressure (PSI)')
    plt.title(plot_title)
    plt.grid(True)
    plt.xlim(-25000, 5000)
    plt.ylim(-3, 43)
    plt.plot(avg_counts, pressure, 'o')
    plt.text(-24500, 1, "Coeffs: " + str(fit_coeffs))
    plt.plot(fit_x, fit_polynomial)
    plt.tight_layout()

    print('Saving ', filename)
    plt.savefig(filename)
    plt.show()

    # add data to dataframe
    stats = [f.name, sensor, adc, degree]
    for c in fit_coeffs[::-1]:  # coeeficients get reversed so they now come low to high
        stats.append(c)
    while len(stats) < len(df.columns):     # pad 0s for extra (missing high order) coefficients
        stats.append(0)
    df = df.append(pd.Series(stats, index=df.columns), ignore_index=True)

filename = os.path.join(Path(sys.argv[1]), 'calibration_coefficients_degree_{}.csv'.format(degree))
print(df)
print('Saving as ', filename)
df.to_csv(filename)
