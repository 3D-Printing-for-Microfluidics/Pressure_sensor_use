'''
Imbed a live animation into a PySimpleGUI frontend, with extra plotting
and sensor control.

Live sensor data gets read from a separate thread and is converted to
PSI using calibration coefficients from a file.

The animation fires on a timer callback from matplotlib and renders to
a PySimpleGUI canvas (which is really just a wrapped tk canvas).

'''

import time
import queue
import threading
import random
from datetime import datetime
import numpy as np
import pandas as pd
import PySimpleGUI as sg
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')


# file to read calibration data from
filename = 'test_data\calibration_coefficients.csv'
coeff = pd.read_csv(filename, index_col=[0])
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
animation_queue = queue.Queue()     # to pass GUI events to animation
raw_data_queue = queue.Queue()      # to pass raw data to main thread
update_rate_ms = 50                 # refresh time in ms
ts, adc0, adc1 = [], [], []         # live data containers

# read fit coeffiecients and calculate PSI
def calculate_psi(counts, sensor, adc, deg=1):
    coef = coeff.iloc[:, -4:][(coeff['Sensor'] == sensor) & (coeff['ADC'] == adc) &
                              (coeff['Degree'] == deg) ].to_numpy().flatten()[::-1]
    return float(np.polyval(coef, counts))

# read the currently selected sensors from the GUI message
def get_sensors(msg):
    names = np.array(['A', 'B', 'C'])
    s0 = [msg[2], msg[3], msg[4]]       # adc0 sensor
    s1 = [msg[6], msg[7], msg[8]]       # adc1 sensor
    return(names[s0][0], names[s1][0])  # boolean index to the names

# thread to continuously poll data from sensors
def data_collection_thread(data_queue, falsify=False):
    if falsify: # simulate some data for development
        t = 0
        while True:
            t += 1
            x = np.sin(np.pi*t/112)*12000-10000
            y = random.randrange(-23000, 3000)
            line = '{},{},{}'.format(t, x, y)
            data_queue.put(line)
            time.sleep(0.001)
    else:
        # ser.read() will go here
        pass

# process all data on queue from the data collection thread
def process_data(data_queue, message, t, x, y):
    s = get_sensors(message)
    while not data_queue.empty():
        line = data_queue.get()
        t0, v0, v1 = line.split(',')
        t.append(float(t0))
        x.append(calculate_psi(float(v0), sensor=s[0], adc=0))
        y.append(calculate_psi(float(v1), sensor=s[1], adc=1))
        data_queue.task_done()
    try:                        # truncate to appropriate window size
        n = int(message[0])
        return t[-n:], x[-n:], y[-n:]
    except (ValueError, TypeError):
        return t, x, y  # don't truncate if there is a bad window size

def animate(_, q):
    # get last message on event queue
    message = None
    while not q.empty():
        message = q.get_nowait()
        q.task_done()

    # plot last n datapoints
    try:
        n = int(message[1][0])  # parse window size
        adc0_window = adc0[-n:]
        adc1_window = adc1[-n:]
        ts_window = [i for i in range(len(adc0_window))]
        ax.clear()
        if message[1][1]:       # if adc0 enable checkbox is checked
            ax.plot(ts_window, adc0_window, 'C0', label='adc0')
            ax.legend(loc='lower right')
        if message[1][5]:       # if adc0 enable checkbox is checked
            ax.plot(ts_window, adc1_window, 'C1', label='adc1')
            ax.legend(loc='lower right')
        ax.set_title('Live Sensor Readings')
        ax.set_xlabel('Time (ms)')
        ax.set_ylabel('Pressure (psi)')

        # save displayed data
        if message[0] == 'Save':
            basename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            data = pd.DataFrame({'timestamp': ts_window, 'adc0': adc0_window, 'adc1': adc1_window})
            data.to_csv(basename + '.csv')
            plt.savefig(basename + '.png')
    except (ValueError, TypeError):
        pass    # ignore poorly formatted messages from the GUI

layout = [
    [   # row 1, some control buttons
        sg.Text('Window Size (ms):'),
        sg.Input(size=(5, 0), default_text=100),
        sg.Button('Start'),
        sg.Button('Pause'),
        sg.Button('Save'),
        sg.Button('Exit')
    ],
    [   # row 2, the animation
        sg.Canvas(key='-CANVAS-')
    ],
    [  # row 3, some frames for the ADC options
        sg.Frame(title='ADC 0', relief=sg.RELIEF_SUNKEN,
                 layout=[[sg.Checkbox('Enabled', default=True)],
                         [sg.Radio('Sensor A', 1, default=True),
                          sg.Radio('Sensor B', 1),
                          sg.Radio('Sensor C', 1)]]),
        sg.Frame(title='ADC 1', relief=sg.RELIEF_SUNKEN,
                 layout=[[sg.Checkbox('Enabled', default=True)],
                         [sg.Radio('Sensor A', 2),
                          sg.Radio('Sensor B', 2, default=True),
                          sg.Radio('Sensor C', 2)]])
    ]
]

# MUST maintain this order: define animation, plt.draw(), setup window
# with finalize=True, then create, draw and pack the TkAgg canvas
ani = animation.FuncAnimation(fig, animate, interval=update_rate_ms, fargs=(animation_queue,))
plt.draw()  # must call plot.draw() to start the animation
window = sg.Window('Read Pressure Sensors', layout, finalize=True, element_justification='center',
                   font='18')

# tie matplotlib renderer to pySimpleGui canvas
figure_canvas_agg = FigureCanvasTkAgg(fig, window['-CANVAS-'].TKCanvas)
figure_canvas_agg.draw()
figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

threading.Thread(target=data_collection_thread, args=(raw_data_queue, True), daemon=True).start()
data_collection_enable = True

while True: # main event loop for GUI
    event, values = window.read(timeout=update_rate_ms)
    # check for button events
    if event in ('Exit', None):
        break
    if event == 'Start':
        data_collection_enable = True
    if event == 'Pause':
        data_collection_enable = False
    # send GUI events to animation
    animation_queue.put_nowait((event, values))
    # process data when not paused
    if data_collection_enable:
        ts, adc0, adc1 = process_data(raw_data_queue, values, ts, adc0, adc1)
    else:   # if paused, throw away live data
        while not raw_data_queue.empty():
            raw_data_queue.get()
            raw_data_queue.task_done()

window.close()
