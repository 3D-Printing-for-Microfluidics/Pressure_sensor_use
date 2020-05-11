

# How to calibrate and use Honeywell 24PC Series pressure sensors with Teensy 3.2

## Install software on Teensy

  1. Install Arduino IDE
      * https://www.arduino.cc/en/Main/Software
  2. Install Teensyduino, dowload and instructions are available here
      * https://www.pjrc.com/teensy/td_download.html
  3. Plug in Teensy and select proper board and port
      * Tools -> Board -> Teensy 3.1/3.2
      * Tools -> Port -> Select Teensy Port
  4. Download and open appropriate `.ino` file and Click 'Upload'

## Pull data with Python

Use one of the scripts here or write your own to find and pull data from the serial port.

Sending `s ####` will set the sampling period to #### us. We usually operate pulling data every 1 ms (`s 10000`).
Sending `s` or `s 0` will stop sampling.
