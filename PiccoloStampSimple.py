#!/usr/bin/python2
from __future__ import division
from serial import Serial
import struct, sys, time, FPS, smtplib, random
import RPi.GPIO as GPIO
from configobj import ConfigObj
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

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


mailVariations = [  'Romain Cazier<br>romain.cazier@gmail.com',
                    'Cyril Diagne<br>cyril.diagne@gmail.com',
                    'Patrick Keller<br>ptrck.kllr@gmail.com',
                    'Guillaume Cerdeira<br>guillaume.ce@gmail.com',
                    'Sebastian Vargas<br>sebastian.vargas@kairosworks.net',
                    'Pauline Saglio<br>pauline.saglio@ecal.ch',
                    'Etienne Malapert<br>etienne.malapert@ecal.ch',
                    'Blinie Saglio<br>blinie@outlook.fr',
                    'Nicolas-Guy Kunz<br>ng.kunz@gmail.com',
                    'Maxime Castelli<br>maximecastelli@yahoo.fr',
                    'Hugo Simon<br>hugosimon@me.com',
                    'Christophe Guignard<br>christophe@fabric.ch',
                    'Charlotte Nicod<br>nicodcharlotte@gmail.com',
                    'Gael / sold-out.ch <gael@sold-out.ch>',
                    'Clemence Chatel<br>clemence_1403@hotmail.fr' ]

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
    sendXY(1000,1000)
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

def turnOffFingerprintLED():
    fps =  FPS.FPS_GT511C3(device_name='/dev/ttyAMA0',baud=9600,timeout=3,is_com=False)
    time.sleep(2)
    fps.SetLED(False)
    time.sleep(1)
    fps.Close()

def sendFinalMail():
    config = ConfigObj('/home/pi/SensibleData/latestMailAdr.cfg')
    try:
        latestAddress = config['address']
        latestName = config['name']
        sendMail(latestAddress, latestName)
        config['address'] = ""
        config['name'] = "" 
        config.write()
    except Exception, e:
    	print "Couldn't send mail: %s" % e

def sendMail(reciever, recieverName):
    # Define these once; use them twice!
    strFrom = 'Sensible Data <sensibledata@icloud.com>'

    # Create the root message and fill in the from, to, and subject headers
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = 'Confirmation'
    msgRoot['From'] = strFrom
    msgRoot['To'] = reciever
    msgRoot.preamble = 'This is a multi-part message in MIME format.'

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    msgText = MIMEText('Hi \n\nPlease allow displaying HTML messages. \n\nKind regards\nSensible Data')
    msgAlternative.attach(msgText)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText('Dear '+recieverName+',<br><br>Thanks for your contribution. Please find enclosed a contact whose portrait was drawn with an amount of lines similar to yours.<br><br>'+random.choice(mailVariations)+'<br><br>Wishing to get more data from you soon, kind regards,<br><br>Sensible Data Administration<br><br><img src="cid:image1">', 'html')
    msgAlternative.attach(msgText)

    # This example assumes the image is in the current directory
    fp = open('/home/pi/SensibleData/sensibledata2.png', 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()

    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    msgRoot.attach(msgImage)

    # Send the email (this example assumes SMTP authentication is required)
    smtp = smtplib.SMTP("smtp.mail.me.com", 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.login('sensibledata@icloud.com', 'Verys3nsible')
    smtp.sendmail(strFrom, reciever, msgRoot.as_string())
    smtp.close()

if __name__ == '__main__':
    while True:
        if GPIO.input(4) == False:
            first_pressed_time=time.time()
            while GPIO.input(4)==False: #call: is button still pressed
                pressed_time=time.time()-first_pressed_time
                print "pressed time: "+str(pressed_time)
                if pressed_time>2 and pressed_time<8:
                    doStamp()
                    turnOffFingerprintLED()
                    time.sleep(5)
                    sendFinalMail()
                time.sleep(0.5)
        time.sleep(0.1)
