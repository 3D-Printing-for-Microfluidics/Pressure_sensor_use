import serial

ser = serial.Serial('COM3', 115200, timeout=5)  # select appropriate COM port. Will timeout after 5 seconds of inactivity
ser.flushInput()                                # clear input buffer

# read, decode, and print to stdout
while True:
    print(ser.readline().decode())
