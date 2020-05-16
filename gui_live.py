'''
Imbed a live animation into a GUI.

Base functionality is there, need to add sensor and adc selection,
and options to pause acquisition and save plots and data.

'''

import sys

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


# set up live plot
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

def animate(_, n):
    try:
        # grab some data
        graph_data = open('test_out_static.csv', 'r').read()
        lines = graph_data.split('\n')
        ts = []
        adc0 = []
        adc1 = []
        for line in lines:
            if len(line) > 1:
                t, v0, v1 = line.split(',')
                ts.append(float(t))
                adc0.append(psi(float(v0)))
                adc1.append(psi(float(v1)))

        # plot last n datapoints
        ax.clear()
        ax.plot(ts[-n:], adc0[-n:], label='adc0')
        ax.plot(ts[-n:], adc1[-n:], label='adc1')
        ax.set_title('Live Sensor Readings')
        ax.set_xlabel('Time (ms)')
        ax.set_ylabel('Pressure (psi)')
        ax.legend(loc='lower right')
        # fig.tight_layout()
    except FileNotFoundError:
        exit()


window_size = 100
ani = animation.FuncAnimation(fig, animate, interval=500, fargs=(window_size,))
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


# button callback functions
def start_callback():
    print('start')
def stop_callback():
    print('stop')
def save_callback():
    print('save')
def saveas_callback():
    print('save as')

# lookup dictionary that maps buttons to callbacks
callbacks = {
    'Start': start_callback,
    'Stop': stop_callback,
    'Save': save_callback,
    'Save As...': saveas_callback,
}

# main event loop
while True:

    event, values = window.read()
    if event in ('Exit', None):
        break

    # lookup event in function dictionary
    if event in callbacks:
        func_to_call = callbacks[event]   # get function from callback dictionary
        func_to_call()
    else:
        print('Event {} not in dispatch dictionary'.format(event))

    print(values)
    print(values[0])
    print('ADC0: enabled:{}, {} {} {}'.format(values[1], values[2], values[3], values[4]))
    print('ADC1: enabled:{}, {} {} {}'.format(values[5], values[6], values[7], values[8]))

window.close()
