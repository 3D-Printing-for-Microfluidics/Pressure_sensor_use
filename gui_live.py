'''
Imbed a live animation into a GUI.

Base functionality is there, need to add sensor and adc selection,
and options to pause acquisition and save plots and data.

'''

import sys
import time
import queue
import threading
import random

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
def process_data(data_queue, t, x, y):
    while not data_queue.empty():
        line = data_queue.get()
        t0, v0, v1 = line.split(',')
        t.append(float(t0))
        x.append(psi(float(v0)))
        y.append(psi(float(v1)))
        data_queue.task_done()
    return t[-window_size:], x[-window_size:], y[-window_size:]

# set up live plot
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
ui_queue = queue.Queue()
data_collection_queue = queue.Queue()
update_rate_ms = 50 # refresh time in ms

# data containers
ts, adc0, adc1 = [], [], []

def animate(_, n, q):
    while not q.empty():
        message = q.get_nowait()
        print('Got a message from GUI: ', message)
        q.task_done()

    # plot last n datapoints
    adc0_window = adc0[-n:]
    adc1_window = adc1[-n:]
    # ts_window = ts[-n:]                               # moving, real time timestamps
    ts_window = [i for i in range(len(adc0_window))]    # static timestams
    ax.clear()
    ax.plot(ts_window, adc0_window, label='adc0')
    ax.plot(ts_window, adc1_window, label='adc1')
    ax.set_title('Live Sensor Readings')
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Pressure (psi)')
    ax.set_ylim(-5, 45)
    ax.legend(loc='lower right')
    # fig.tight_layout()


window_size = 100
ani = animation.FuncAnimation(fig, animate, interval=update_rate_ms, fargs=(window_size, ui_queue))
plt.draw()  # must call plot.draw() to start the animation

# helper function to pass matplotlib backend to pySimpleGui canvas
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


#################### Normal PySimpleGUI Stuff ##########################

layout = [
    [   # row 1
        sg.Text('Window Size (ms):'),
        sg.Input(size=(5, 0), default_text=100),
        sg.Button('Start'),
        sg.Button('Stop'),
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
window = sg.Window('Pressure Sensors', layout, finalize=True, element_justification='center', font='18')

# add the plot to the window
fig_canvas_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)

# start a thread that continuously collects data
threading.Thread(target=data_collection_thread, args=(data_collection_queue,True), daemon=True).start()

# main event loop frr GUI
while True:

    event, values = window.read(timeout=update_rate_ms)

    # check for exit
    if event in ('Exit', None):
        break

    # send data to animation function
    ui_queue.put_nowait(event)

    # update data containers
    print(len(ts), data_collection_queue.qsize())
    ts, adc0, adc1 = process_data(data_collection_queue, ts, adc0, adc1)
    print(len(ts), data_collection_queue.qsize(), ui_queue.qsize())

window.close()
