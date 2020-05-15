'''
Simulate live data by writing random data in the
valid sensor range to a temporary file every 10 ms.

'''

import random
import time
import os

filename = 'test_out.csv'
timestamp = 0

while True:
    try:
        timestamp += 1
        adc0 = random.randrange(-25000, 5000)
        adc1 = random.randrange(-25000, 5000)

        line = '{},{},{}\n'.format(timestamp, adc0, adc1)

        print(line, end='')
        with open(filename, 'a') as f:
            f.write(line)
        time.sleep(.1)
    except KeyboardInterrupt:
        os.remove(filename)
        break
