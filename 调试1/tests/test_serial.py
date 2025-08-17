import serial
import sys, os
sys.path.append(os.getcwd() + '\\code')

from models.MoveControl import MoveControl


if __name__ == '__main__':
    serial_port = '/dev/ttyUSB0'
    serial_baud_rate = 115200

    mc = MoveControl(port = serial, baudrate = serial_baud_rate)

    

