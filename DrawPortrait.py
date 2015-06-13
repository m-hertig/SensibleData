#!/usr/bin/python

from serial import Serial
from vectorize import Vectorizer
from rasterize import Rasterizer
import struct, sys
import time, os, glob

#INPUT = '4.1.05.tiff'
#INPUT = 'test2.jpg'
#INPUT = 'test_text.png'
#INPUT = 'test4.png'
INPUT = 'martin.png'
#INPUT = 'test5.jpg'
#INPUT = 'test3.png'
#INPUT = 'lena.bmp'
#INPUT = 'test_pattern.jpg'
COMMAND_CONNECT = 'C'; # connect byte from computer
COMMAND_SEND_NEXT = 'B'; # send the next packet from piccolo
COMMAND_READY = 'A'; # piccolo ready to plot! from piccolo
COMMAND_POS_START_BYTE = 'P'; # start of position from computer
COMMAND_POS_END_BYTE = ';'; # end of position from computer
COMMAND_END_STACK = 'E'; # finished sending current stack. from computer
RES_X = 160

MAX_X =  2480
MIN_X = -2480

MAX_Y =  2480
MIN_Y = -2480

SERIAL_PORT = '/dev/ttyACM1'
BAUD        = 115200

END_DATA    = struct.pack('<IIb', 0xFFFF1111, 0xFFFF1111, 0x11)

handshakeDone = False

def map_range(a, b1, b2, x1, x2):
    return (float(a - b1) / float(b2 - b1)) * (x2 - x1) + x1

def send_wait_ack(data):
    global serial
    serial.write(COMMAND_POS_START_BYTE)
    serial.write(data)
    serial.write(COMMAND_POS_END_BYTE)
    # waiting piccolos confirmation
    # time.sleep(0.02)
    serial.read(3)

def main():
    global serial, MIN_Y, MAX_Y, MIN_X, MAX_X

    # if not len(sys.argv) == 2:
    #     print 'Wrong args'
    #     sys.exit(0)
    
    # RES_X = int(sys.argv[1])
    RES_X = 400

    latestImagePath = max(glob.iglob('/home/pi/SensibleData/images/*.jpg'), key=os.path.getctime)

    if RES_X < 0:
        data   = Rasterizer()
        points = data.get_lines(latestImagePath, MIN_X, MAX_X, MIN_Y, MAX_Y)
    else:
        data   = Vectorizer()
        points = data.get_polygons(latestImagePath, RES_X, MIN_X, MAX_X, MIN_Y, MAX_Y)

    serial = Serial(SERIAL_PORT, BAUD)
    serial.flushInput()
    serial.flushOutput()

    # if not handshakeDone:
    #     print 'Waiting for Piccolo'

    #     serial.write(COMMAND_CONNECT)
    #     # Wait until the mcu sends a byte, signaling it's ready
    #     serial.read(6)
    #     handshakeDone = True

    print 'Waiting for Piccolo'

    serial.write(COMMAND_CONNECT)
    # Wait until Piccolo sends a byte, signaling it's ready
    # serial.read(6)
    # TODO: really reading handshake instead of flushing it. problem is that the script attempts to
    # do a handshake everytime it is executed, but piccolo only responds once
    time.sleep(0.2)
    serial.flushInput()

    print 'Starting transmission'

    count = 1
    for cur_p in points:
        next_x = cur_p[0]
        next_y = cur_p[1]
        next_z = cur_p[2]
        data = struct.pack('iii', next_x, next_y, next_z);
        send_wait_ack(data)

        print 'Sent point %d of %d. x: %d, y: %d, z: %d' %(count, len(points), next_x,next_y,next_z)
        count += 1

    time.sleep(0.3)
    # Send end of transmission
    serial.write(COMMAND_END_STACK)
    print 'End Stack command sent'
    time.sleep(1)
    serial.flushInput()
    serial.flushOutput()
    serial.close();
    # raw_input("press enter to continue")

if __name__ == '__main__':
    main()
