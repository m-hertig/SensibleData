#!/usr/bin/python2
from __future__ import division
from serial import Serial
import struct, sys
import time
import RPi.GPIO as GPIO

# SERIAL_PORT = '/dev/tty.usbmodemfa141'
SERIAL_PORT = '/dev/ttyACM2'
BAUD        = 115200

COMMAND_CONNECT = 'C'; # connect byte from computer
COMMAND_SEND_NEXT = 'B'; # send the next packet from piccolo
COMMAND_READY = 'A'; # piccolo ready to plot! from piccolo
COMMAND_POS_START_BYTE = 'P'; # start of position from computer
COMMAND_END_BYTE = ';'; # end of position from computer
COMMAND_END_STACK = 'E'; # finished sending current stack. from computer
RES_X = 160

MAX_X =  2500
MIN_X = -2500
MAX_Y =  2500
MIN_Y = -2500
MAX_Z =  2000
MIN_Z = -2000


Z_DOWN_STAMP_POS = -400
Z_UP_POS = Z_DOWN_STAMP_POS+2500
Z_DOWN_INK_POS = Z_DOWN_STAMP_POS + 400  

INKPOS_X = MIN_X
INKPOS_Y = MIN_Y

currentX = MIN_X
currentY = MIN_Y
currentZ = MAX_Z

GPIO.setmode(GPIO.BCM)

GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def map_range(a, b1, b2, x1, x2):
    return (float(a - b1) / float(b2 - b1)) * (x2 - x1) + x1


def sendXYZ(xPos,yPos,zPos):
    global serial,currentX,currentY,currentZ
    serial.write(COMMAND_POS_START_BYTE)
    serial.write(struct.pack('i',xPos))
    serial.write(struct.pack('i',yPos))
    serial.write(struct.pack('i',zPos))
    serial.write(COMMAND_END_BYTE)
    # waiting piccolos confirmation
    serial.read(3)
    currentX = xPos
    currentY = yPos
    currentZ = zPos
    # time.sleep(0.1)
    
def sendZ(zPos):
    global currentX,currentY,currentZ
    sendXYZ(currentX,currentY,zPos)
    currentZ = zPos

def sendXY(xPos, yPos):
    global currentX,currentY,currentZ
    sendXYZ(xPos, yPos, currentZ)
    currentX = xPos
    currentY = yPos

def zDownAndUpStamp():
    sendZ(Z_DOWN_STAMP_POS)
    time.sleep(0.2)
    sendZ(Z_DOWN_STAMP_POS+400)
    sendZ(Z_DOWN_STAMP_POS)
    time.sleep(0.2)
    sendZ(Z_UP_POS)

def zDownAndUpInk():
    sendZ(Z_DOWN_INK_POS)
    # time.sleep(0.2)
    sendZ(Z_UP_POS)

def getInk():
    global Z_UP_POS,INKPOS_X,INKPOS_Y

    sendZ(Z_UP_POS)
    # sendXY(0,0)
    # time.sleep(0.5)
    sendXY(INKPOS_X,INKPOS_Y)
    zDownAndUpInk()
    sendXY(INKPOS_X+100,INKPOS_Y+100)
    zDownAndUpInk()


def doStamp():
    global serial, MIN_Y, MAX_Y, MIN_X, MAX_X

    serial = Serial(SERIAL_PORT, BAUD)
    serial.flushInput()
    serial.flushOutput()

    print 'Waiting for Piccolo'

    serial.write(COMMAND_CONNECT)
    # Wait until Piccolo sends a byte, signaling it's ready
    serial.read(6)
    # TODO: really reading handshake instead of flushing it. problem is that the script attempts to
    # do a handshake everytime it is executed, but piccolo only responds once
    serial.flushInput()
    sendZ(Z_UP_POS)
    getInk();
    sendXY(100,000)
    zDownAndUpStamp()
    time.sleep(0.5)
    # Send end of transmission
    serial.write(COMMAND_END_STACK)
    print 'End Stack command sent'
    time.sleep(2)
    serial.flushInput()
    serial.flushOutput()
    serial.close()
    # raw_input("press enter to continue")

if __name__ == '__main__':
    while True:
        input_state = GPIO.input(4)
        if input_state == False:
            print('Button Pressed')
            doStamp()
            time.sleep(6)
        time.sleep(0.1)
