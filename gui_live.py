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

filename = sys.argv[1]  # file to read calibration data from
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
ax1 = fig.add_subplot(1, 1, 1)

def animate(_):
    try:
        # grab some data
        graph_data = open('test_out.csv', 'r').read()
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
        n = 50
        ax1.clear()
        ax1.plot(ts[-n:], adc0[-n:], label='adc0')
        ax1.plot(ts[-n:], adc1[-n:], label='adc1')
        ax1.set_title('Live Sensor Readings')
        ax1.set_xlabel('Time (ms)')
        ax1.set_ylabel('Pressure (psi)')
        ax1.legend(loc='lower right')
        # fig.tight_layout()
    except FileNotFoundError:
        exit()

ani = animation.FuncAnimation(fig, animate, interval=500)
plt.draw()  # must call plot.draw() to start the animation

# helper function to pass matplotlib backend to pySimpleGui canvas
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


#################### Normal PySimpleGUI Stuff ##########################

# define the window layout
layout = [[sg.Text('Pressure Sensors')],
          [sg.Canvas(key='-CANVAS-')],
          [sg.Button('Exit')]]

# create the form and show it
window = sg.Window('Pressure Sensors', layout, finalize=True, element_justification='center', font='18')

# add the plot to the window
fig_canvas_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)

event, values = window.read()

window.close()
