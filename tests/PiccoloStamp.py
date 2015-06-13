#!/usr/bin/python2
from __future__ import division
from serial import Serial
import struct, sys
import time
import RPi.GPIO as GPIO

# SERIAL_PORT = '/dev/tty.usbmodemfa141'
SERIAL_PORT = '/dev/ttyACM0'
BAUD        = 115200

COMMAND_CONNECT = 'C'; # connect byte from computer
COMMAND_SEND_NEXT = 'B'; # send the next packet from piccolo
COMMAND_READY = 'A'; # piccolo ready to plot! from piccolo
COMMAND_ROTATE_START_BYTE = 'R'; # start of position from computer
COMMAND_POS_START_BYTE = 'P'; # start of position from computer
COMMAND_END_BYTE = ';'; # end of position from computer
COMMAND_END_STACK = 'E'; # finished sending current stack. from computer
RES_X = 160

MAX_X =  2500
MIN_X = -2500
MAX_Y =  2500
MIN_Y = -2500
MAX_Z =  2500
MIN_Z = -2500

MAX_LETTERS = 15
letterIndex = 0

Z_UP_POS = MAX_Z
Z_DOWN_STAMP_POS = -2200
Z_DOWN_INK_POS = Z_DOWN_STAMP_POS + 100  

INKPOS_X = MAX_X
INKPOS_Y = MAX_Y

currentX = MIN_X
currentY = MIN_Y
currentZ = MAX_Z

letterCount = 32
fullturnSteps = 2038

isAtMagnet = False

# internal / calculated
stepsPerLetter = fullturnSteps / letterCount
print stepsPerLetter
currentStep = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(4, GPIO.RISING)


def magnetDetected(infos):
    global isAtMagnet
    isAtMagnet = True
    print 'MAGNET!'

GPIO.add_event_callback(4, magnetDetected)

def calibrate():
    global isAtMagnet
    isAtMagnet = False
    for x in range(fullturnSteps):
        sendRotation(1)
        if isAtMagnet:
            currentStep = 63
            break


def map_range(a, b1, b2, x1, x2):
    return (float(a - b1) / float(b2 - b1)) * (x2 - x1) + x1

def sendRotation(steps):
    global serial, fullturnSteps
    if (steps>fullturnSteps/2):
        steps=-(fullturnSteps - steps)
    serial.write(COMMAND_ROTATE_START_BYTE)
    serial.write(struct.pack('i',steps))
    serial.write(COMMAND_END_BYTE)
    # waiting piccolos confirmation
    print 'stepped: '+str(steps)+' steps'
    serialResponse = serial.read(3)
    # time.sleep(0.001)
    print "serial response: "+str(serialResponse)

def sendPos(data):
    global serial
    serial.write(COMMAND_POS_START_BYTE)
    serial.write(data)
    serial.write(COMMAND_END_BYTE)
    # waiting piccolos confirmation
    time.sleep(0.1)
    serial.read(3)
    

def sendXYZ(xPos,yPos,zPos):
    global currentX,currentY,currentZ
    data = struct.pack('iii', xPos, yPos, zPos)
    sendPos(data)
    currentX = xPos
    currentY = yPos
    currentZ = zPos
    
def sendZ(zPos):
    global currentX,currentY,currentZ
    data = struct.pack('iii', currentX, currentY, zPos)
    sendPos(data)
    currentZ = zPos

def sendXY(xPos, yPos):
    global currentX,currentY,currentZ
    data = struct.pack('iii', xPos, yPos, currentZ)
    sendPos(data)
    currentX = xPos
    currentY = yPos

def zDownAndUpStamp():
    sendZ(Z_DOWN_STAMP_POS)
    time.sleep(0.2)
    sendZ(Z_UP_POS)

def zDownAndUpInk():
    sendZ(Z_DOWN_STAMP_POS)
    time.sleep(0.2)
    sendZ(Z_UP_POS)

def getInk():
    global Z_UP_POS,INKPOS_X,INKPOS_Y

    sendZ(Z_UP_POS)
    sendXY(INKPOS_X,INKPOS_Y)
    zDownAndUpInk()

def stampLetter():
    global letterIndex
    myLetterXPos, myLetterYPos = calcLetterPos()
    print "letter x pos: "+str(myLetterXPos)
    print "letter y pos: "+str(myLetterYPos)
    sendXY(myLetterXPos,myLetterYPos)
    zDownAndUpStamp()
    letterIndex += 1

def makeSpace():
    global letterIndex
    letterIndex +=1

def calcLetterPos():
    global MAX_X,MIN_X,MAX_LETTERS,letterIndex
    offset = MAX_X - MIN_X
    spacePerLetter = offset/MAX_LETTERS
    currentLetterX = letterIndex%MAX_LETTERS
    currentLetterY = letterIndex/MAX_LETTERS
    letterXPos = currentLetterX*spacePerLetter
    letterYPos = currentLetterY*spacePerLetter
    return (letterXPos,letterYPos)
    

def main():
    global serial, MIN_Y, MAX_Y, MIN_X, MAX_X

    serial = Serial(SERIAL_PORT, BAUD)
    serial.flushInput()
    serial.flushOutput()

    print 'Waiting for Piccolo'

    # serial.write(COMMAND_CONNECT)
    # Wait until Piccolo sends a byte, signaling it's ready
    # serial.read(6)
    # TODO: really reading handshake instead of flushing it. problem is that the script attempts to
    # do a handshake everytime it is executed, but piccolo only responds once
    # serial.flushInput()

    # sendRotation(fullturnSteps)
    testText = "AQL"
    letterList = list(testText)
    # sendXY(INKPOS_X,INKPOS_Y)
    # time.sleep(2)
    print 'at INKPOS'
    # calibrate()

    while True:
        for letter in letterList:
            global currentStep
            letterUnicodeIndex = ord(letter)
            if (letter==" "):
                makeSpace()
            else:
                if(letter=="."):
                    letterUnicodeIndex=91
                if(letter==","):
                    letterUnicodeIndex=92
                if(letter=="!"):
                    letterUnicodeIndex=93
                if(letter=="?"):
                    letterUnicodeIndex=94
                if(letter=="("):
                    letterUnicodeIndex=95
                if(letter==")"):
                    letterUnicodeIndex=96
                posInAlphabet = (letterUnicodeIndex-65)
                nextStep = posInAlphabet*-stepsPerLetter
                # due to unprecise stepper that says it is 1/64 but is not really I add some steps
                stepsToAdd = posInAlphabet/3
                nextStep = nextStep-stepsToAdd
                stepsToTake = (nextStep - currentStep)
                sendRotation(stepsToTake)
                currentStep = nextStep
                print 'Stepped to '+letter+', '+str(stepsToTake)+' steps'
                time.sleep(0.5)
                # getInk()
                print 'got ink'
                stampLetter()
                print 'letter stamped'

    time.sleep(0.3)
    # sendXY(MIN_X,MAX_Y)
    # sendZ(Z_UP_POS)
    stepsToZero = -currentStep
    sendRotation(stepsToZero)
    print 'Stepped to zero'
    time.sleep(1)
    # Send end of transmission
    serial.write(COMMAND_END_STACK)
    print 'End Stack command sent'
    time.sleep(1)
    serial.flushInput()
    serial.flushOutput()
    serial.close()
    # raw_input("press enter to continue")

if __name__ == '__main__':
    main()
