'''
Imbed a live animation into a GUI.

Base functionality is there, need to add sensor and adc selection,
and options to pause acquisition and save plots and data.

'''

import time
import queue
import threading
import random
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import PySimpleGUI as sg

matplotlib.use('TkAgg') # not sure if this is necessary

filename = 'test_data\calibration_coefficients.csv'  # file to read calibration data from
df = pd.read_csv(filename, index_col=[0])

# reads the fit coeffiecients from the calibration file
def get_coef(sensor, adc, deg=1):
    return df.iloc[:, -4:][(df['Sensor'] == sensor) &
                           (df['ADC'] == adc) &
                           (df['Degree'] == deg)
                          ].to_numpy().flatten()[::-1]

def psi(counts, sensor='A', adc=0):
    coef = get_coef(sensor=sensor, adc=adc)
    return float(np.polyval(coef, counts))

def data_collection_thread(data_queue, falsify=False):
    if falsify: # simulate some data for development
        t = 0
        while True:
            t += 1
            x = np.sin(np.pi*t/112)*12000-10000
            y = random.randrange(-23000, 3000)
            line = '{},{},{}'.format(t, x, y)
            data_queue.put(line)  # put a message into queue for GUI
            time.sleep(0.001)   # sleep about 1ms
    else:
        # ser.read() will go here
        pass


# process all data on queue
def process_data(data_queue, settings_queue, t, x, y):
    message = None

    # get the most recent message from the GUI
    while not settings_queue.empty():
        message = settings_queue.get_nowait()
        settings_queue.task_done()

    '''
    0 - window size
    1 - ADC0 enable
    2, 3, 4 - ADC 0 sensor select
    5 - ADC1 enable
    6,7,8 - ADC 1 sensor select
    '''

    # process data from the data collection thread
    while not data_queue.empty():
        line = data_queue.get()
        t0, v0, v1 = line.split(',')
        t.append(float(t0))
        x.append(psi(float(v0)))
        y.append(psi(float(v1)))
        data_queue.task_done()

    try:
        n = int(message[1][0])
        return t[-n:], x[-n:], y[-n:]
    except (ValueError, TypeError) as e:
        return t, x, y  # don't truncate the data if there is a poorly formatted message

# set up live plot
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
animation_queue = queue.Queue()
raw_data_queue = queue.Queue()
data_settings_queue = queue.Queue()

update_rate_ms = 50 # refresh time in ms

# data containers
ts, adc0, adc1 = [], [], []

def animate(_, q):
    message = None

    # get last message on event queue
    while not q.empty():
        message = q.get_nowait()
        q.task_done()

    try:
        n = int(message[1][0])                              # parse window size

        # plot last n datapoints
        adc0_window = adc0[-n:]
        adc1_window = adc1[-n:]
        # ts_window = ts[-n:]                               # moving, real time timestamps
        ts_window = [i for i in range(len(adc0_window))]    # static timestams
        ax.clear()
        if message[1][1]:                                   # if adc0 enable checkbox is checked
            ax.plot(ts_window, adc0_window, 'C0', label='adc0')
            ax.legend(loc='lower right')
        if message[1][5]:                                   # if adc0 enable checkbox is checked
            ax.plot(ts_window, adc1_window, 'C1', label='adc1')
            ax.legend(loc='lower right')
        ax.set_title('Live Sensor Readings')
        ax.set_xlabel('Time (ms)')
        ax.set_ylabel('Pressure (psi)')

        # save displayed data
        if message[0] == 'Save':
            basename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            data = pd.DataFrame({'timestamps': ts_window,
                                 'adc0': adc0_window,
                                 'adc1': adc1_window})
            data.to_csv(basename + '.csv')
            plt.savefig(basename + '.png')

        # ax.set_ylim(-5, 45)
        # fig.tight_layout()
    except (ValueError, TypeError) as e:
        pass    # ignore poorly formatted messages


window_size = 1000
ani = animation.FuncAnimation(fig, animate, interval=update_rate_ms,
                              fargs=(animation_queue,))
plt.draw()  # must call plot.draw() to start the animation

# helper function to pass matplotlib backend to pySimpleGui canvas
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both',
                                           expand=1)
    return figure_canvas_agg

layout = [
    [   # row 1, some control buttons
        sg.Text('Window Size (ms):'),
        sg.Input(size=(5, 0), default_text=100),
        sg.Button('Start'),
        sg.Button('Pause'),
        sg.Button('Save'),
        sg.FileSaveAs(),
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

# create the form and show it
window = sg.Window('Pressure Sensors', layout, finalize=True,
                   element_justification='center', font='18')

# add the plot to the window
fig_canvas_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)

# start a thread that continuously collects data
threading.Thread(target=data_collection_thread,
                 args=(raw_data_queue, True), daemon=True).start()

data_collection_enable = True

# main event loop frr GUI
while True:

    event, values = window.read(timeout=update_rate_ms)

    # check for button events
    if event in ('Exit', None):
        break
    if event == 'Start':
        data_collection_enable = True
    if event == 'Pause':
        data_collection_enable = False

    # send UI data to animation and data reading queues
    animation_queue.put_nowait((event, values))
    data_settings_queue.put_nowait((event, values))

    # process data when not paused
    if data_collection_enable:
        ts, adc0, adc1 = process_data(raw_data_queue,
                                      data_settings_queue, ts,
                                      adc0, adc1)
    else:
        while not raw_data_queue.empty():
            raw_data_queue.get()
            raw_data_queue.task_done()

window.close()
