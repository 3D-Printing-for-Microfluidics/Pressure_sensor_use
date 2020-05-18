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

def data_collection_thread(data_queue):

    # for now, just simulate some random data for development
    t = 0
    while True:
        t += 1
        x = random.randrange(-25000, 5000)
        y = random.randrange(-25000, 5000)
        line = '{},{},{}'.format(t, x, y)
        data_queue.put(line)  # put a message into queue for GUI
        time.sleep(0.001)   # sleep about 1ms

# set up live plot
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
ui_queue = queue.Queue()
data_collection_queue = queue.Queue()


ts = []
adc0 = []
adc1 = []

def animate(_, n, q, data):
    if not q.empty():
        message = q.get_nowait()
        print('Got a message from GUI: ', message)
        q.task_done()
    else:
        message = None

    # process all data on queue
    while not data.empty():
        line = data.get()
        t, v0, v1 = line.split(',')
        ts.append(float(t))
        adc0.append(psi(float(v0)))
        adc1.append(psi(float(v1)))
        data.task_done()
        # print("queue emptied")

    # plot last n datapoints
    ts_window = ts[-n:]
    adc0_window = adc0[-n:]
    adc1_window = adc1[-n:]
    ax.clear()
    ax.plot(ts_window, adc0_window, label='adc0')
    ax.plot(ts_window, adc1_window, label='adc1')
    ax.set_title('Live Sensor Readings')
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Pressure (psi)')
    ax.legend(loc='lower right')
    # fig.tight_layout()


window_size = 100
ani = animation.FuncAnimation(fig, animate, interval=200, fargs=(window_size, ui_queue, data_collection_queue))
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
threading.Thread(target=data_collection_thread, args=(data_collection_queue,), daemon=True).start()

# main event loop frr GUI
while True:

    event, values = window.read(timeout=500)

    # check for exit
    if event in ('Exit', None):
        break

    ui_queue.put_nowait(event)

    ts = ts[-window_size:]
    adc0 = adc0[-window_size:]
    adc1 = adc1[-window_size:]

window.close()
