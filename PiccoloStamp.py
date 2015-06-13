#!/usr/bin/python2
from __future__ import division
from serial import Serial
import struct, sys
import gmail, time, unicodedata

g = gmail.login("sensibledata2@gmail.com", "verysensible")
# import RPi.GPIO as GPIO

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
MAX_Z =  2000
MIN_Z = -2000

passportTexts = ["MARTIN","26     MALE","IIII of 10"]
# passportTexts = ["ABC"]

# if the stepper is wired that it turns backwards
IS_WHEEL_INVERTED = False

MAX_LETTERS = 12
LINE_HEIGHT = 1200
MARGIN_TOP = 1600
letterIndex = 1
lineNr = 0

Z_DOWN_STAMP_POS = -100
Z_UP_POS = Z_DOWN_STAMP_POS+1500
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
currentStep = 0

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# GPIO.add_event_detect(4, GPIO.RISING)

num2words = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', \
             6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten', \
            11: 'Eleven', 12: 'Twelve', 13: 'Thirteen', 14: 'Fourteen', \
            15: 'Fifteen', 16: 'Sixteen', 17: 'Seventeen', 18: 'Eighteen', \
            19: 'Nineteen', 20: 'Twenty', 30: 'Thirty', 40: 'Forty', \
            50: 'Fifty', 60: 'Sixty', 70: 'Seventy', 80: 'Eighty', \
            90: 'Ninety', 0: 'Zero'}

def numberToWords(n):
    try:
        print num2words[n]
    except KeyError:
        try:
            print num2words[n-n%10] + num2words[n%10].lower()
        except KeyError:
            print 'Number out of range'


def magnetDetected(infos):
    global isAtMagnet
    isAtMagnet = True
    print 'MAGNET!'

# GPIO.add_event_callback(4, magnetDetected)

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
    global serial, fullturnSteps, IS_WHEEL_INVERTED
    # if (steps>fullturnSteps/2 and IS_WHEEL_INVERTED==False):
    #     steps=-(fullturnSteps - steps)
    # elif (steps<-(fullturnSteps/2) and IS_WHEEL_INVERTED==True):
    #     steps=fullturnSteps + steps
    serial.write(COMMAND_ROTATE_START_BYTE)
    serial.write(struct.pack('i',steps))
    serial.write(COMMAND_END_BYTE)
    # waiting piccolos confirmation
    print 'stepped: '+str(steps)+' steps'
    serialResponse = serial.read(3)
    # time.sleep(0.001)
    print "serial response: "+str(serialResponse)

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
    # time.sleep(0.2)
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

def gotoLetterXY():
    global letterIndex
    myLetterXPos, myLetterYPos = calcLetterPos()
    print "letter x pos: "+str(myLetterXPos)
    print "letter y pos: "+str(myLetterYPos)
    #sendXY(1500,1500)
    sendXY(myLetterXPos,myLetterYPos)
    letterIndex += 1

def makeSpace():
    global letterIndex
    letterIndex +=1

def calcLetterPos():
    global MAX_X,MIN_X,MAX_LETTERS,LINE_HEIGHT,MARGIN_TOP,letterIndex,lineNr
    offset = MAX_X - MIN_X
    spacePerLetter = offset/MAX_LETTERS
    letterXPos = MIN_X+letterIndex*spacePerLetter
    letterYPos = MAX_Y-lineNr*LINE_HEIGHT-MARGIN_TOP
    # to not grind the gears
    letterXPos = min(MAX_X, letterXPos)
    letterYPos = min(MAX_Y, letterYPos)
    letterXPos = max(MIN_X, letterXPos)
    letterYPos = max(MIN_Y, letterYPos)
    return (letterXPos,letterYPos)
    

def launchStamp():
    global serial, MIN_Y, MAX_Y, MIN_X, MAX_X,letterIndex,lineNr, IS_WHEEL_INVERTED

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

    # sendRotation(fullturnSteps)
    testText = "rather beautiful"

    # sendXY(INKPOS_X,INKPOS_Y)
    # time.sleep(2)
    print 'at INKPOS'
    # calibrate()

    sendZ(Z_UP_POS)

    for text in passportTexts:
    
        if type(text)==int:
            text = str(numberToWords(text))
        # the wheel only has uppercase letters
        text = text.upper()
        letterList = list(text)

        for letter in letterList:
            global currentStep
            letterUnicodeIndex = ord(letter)
            if (letter==" "):
                makeSpace()
            else:
                if(letter=="0"):
                    letterUnicodeIndex=79
                if(letter=="1"):
                    letterUnicodeIndex=73
                if(letter=="2"):
                    letterUnicodeIndex=89
                if(letter=="3"):
                    letterUnicodeIndex=90
                if(letter=="4"):
                    letterUnicodeIndex=91
                if(letter=="5"):
                    letterUnicodeIndex=92
                if(letter=="6"):
                    letterUnicodeIndex=93
                if(letter=="7"):
                    letterUnicodeIndex=94
                if(letter=="8"):
                    letterUnicodeIndex=95
                if(letter=="9"):
                    letterUnicodeIndex=96
                posInAlphabet = (letterUnicodeIndex-65)
                nextStep = posInAlphabet*stepsPerLetter
                # due to unprecise stepper that says it is 1/64 but is not really I add some steps
                stepsToAdd = posInAlphabet/3
                nextStep = nextStep+stepsToAdd
                if IS_WHEEL_INVERTED:
                    nextStep = -nextStep
                stepsToTake = (nextStep - currentStep)
                if stepsToTake<0:
                    stepsToTake=stepsToTake+2038
                sendRotation(stepsToTake)
                currentStep = nextStep
                getInk()
                gotoLetterXY()
                time.sleep(0.2)
                print 'Stepped to '+letter+', '+str(stepsToTake)+' steps'
                zDownAndUpStamp()
                # time.s(0.5)
                print 'got ink'
                print 'letter stamped'

        letterIndex = 1
        lineNr = lineNr+1

    # time.s(0.3)
    sendXY(MIN_X,MAX_Y)
    sendZ(Z_UP_POS)
    stepsToZero = -currentStep
    sendRotation(stepsToZero)
    # print 'Stepped to zero'
    time.sleep(1)
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
        g = gmail.login("sensibledata2@gmail.com", "verysensible")
        unread = g.inbox().mail(unread=True)
        if len(unread)>0: 
            # None

            unread[0].fetch()
            sender = unread[0].fr
            # senderNormalized = unicodedata.normalize('NFKD', sender).encode('ascii', 'ignore')
            # senderSubstring = senderNormalized[:8]
            senderSubstring = sender[:8]
            passportTexts[0] = senderSubstring.upper()
            print "NAME: "+passportTexts[0]
            unread[0].read()
            launchStamp()

            # Dear ...,
        time.sleep(4)
        g.logout()