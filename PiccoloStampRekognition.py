#!/usr/bin/python2
from __future__ import division
from serial import Serial
import struct, sys
import gmail, time, unicodedata
import os, glob, ftplib, urllib
import requests, json, random
import FPS, re
from email.utils import parseaddr
from configobj import ConfigObj
import boto3, pprint
import boto3.session

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
MIN_Y = -2300
MAX_Z =  2000
MIN_Z = -2000

beatuyScore = random.randrange(35, 100);

passportTexts = ["ANON","999     X",str(beatuyScore),"NONE"]
confusedVariations = ["ABSENT","CONFUSED","NEUTRAL","PENSIVE"]
# passportTexts = ["ABC"]

# if the stepper is wired that it turns backwards
IS_WHEEL_INVERTED = False

MAX_LETTERS = 12
LINE_HEIGHT = 1000
MARGIN_TOP = 1600
letterIndex = 1
lineNr = 0

Z_DOWN_STAMP_POS = -410
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

beauty=0.55
age=26
sex="MALE"
highestAttr="NONE"
latestImagePath = ""

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

def gotoInkXY():
    global Z_UP_POS,INKPOS_X,INKPOS_Y

    sendZ(Z_UP_POS)
    # sendXY(0,0)
    # time.sleep(0.5)
    sendXY(INKPOS_X,INKPOS_Y)

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

def uploadLatestImg():
    global latestImagePath
    session = ftplib.FTP('109.239.61.126','336054-90-sensibleData','JRWZr3EH&&cC')
    # latestImagePath = max(glob.iglob('/home/pi/SensibleData/images/*.jpg'), key=os.path.getctime)
    latestImagePath = max(glob.iglob('/home/pi/SensibleData/images/*.jpg'), key=os.path.getctime)
    latestImageFilename = os.path.basename(latestImagePath)
    file = open(latestImagePath,'rb')               # file to send
    session.storbinary('STOR imageToAnalyze.jpg', file)     # send the file
    file.close()                                    # close file and FTP
    session.quit()

def uploadAnalyzedImg():
    global latestImagePath,beauty,age,sex,highestAttr
    session = ftplib.FTP('109.239.61.126','336054-90-sensibleData','JRWZr3EH&&cC')
    # latestImagePath = max(glob.iglob('/home/pi/SensibleData/images/*.jpg'), key=os.path.getctime)
    newFilename = str(int(beauty))+"-"+str(int(age))+"-"+str(sex)+"-"+highestAttr+"-"+str(int(time.time()))+".jpg"
    filenameUrlEncoded = urllib.quote_plus(newFilename)
    storcommand = "STOR "+"images/"+filenameUrlEncoded
    file = open(latestImagePath,'rb')         # file to send
    session.storbinary(storcommand, file)     # send the file
    file.close()                                    # close file and FTP
    session.sendcmd('SITE CHMOD 644 images/' + filenameUrlEncoded)
    session.quit()
    uploadedUrl = "http://idowebsites.ch/sensibleData/images/"+filenameUrlEncoded
    print uploadedUrl

def getFaceAnalysis():
    global passportTexts, beauty, age, sex, highestAttr
    try:
        # Ask both apis rekognition and faceplusplus
        # as rekognition provides better results and faceplusplus provides beauty score
        print "Trying to get aws rekognition Analysis"
        botoSession = boto3.session.Session(region_name='eu-west-1')
        rekognition = boto3.client('rekognition')
        latestImagePath = max(glob.iglob('/home/pi/SensibleData/images/*.jpg'), key=os.path.getctime)
        with open(latestImagePath, 'rb') as source_image:
            source_bytes = source_image.read()

            # s3client = botoSession.client('s3', config= boto3.session.Config(signature_version='s3v4'))
            # bucket_name = "sensiblebucket";
            # s3client.upload_fileobj(source_image, bucket_name, "uploads/"+filename)
            
        response = rekognition.detect_faces(Image={ 'Bytes': source_bytes },Attributes=['ALL'])

        firstPerson = response["FaceDetails"][0]
        emotions = firstPerson["Emotions"]
        # 0 = female, 1 = male
        sex = firstPerson["Gender"]["Value"]
        if sex.lower() == "male":
            sex = "M"
        elif sex.lower() == "female":
            sex = "F"
        age = str(int((firstPerson["AgeRange"]["High"] + firstPerson["AgeRange"]["Low"])/2))
        highestVal = 0
        highestAttr = ""
        moods = {}
        for emotion in emotions:
            att = emotion['Type'].lower()
            val = int(round(emotion['Confidence']))
            moods[att] = val

        for att,val in moods.iteritems():
            print att,val
            if val>highestVal:
                highestVal = val
                highestAttr = att
        if highestVal < 0.15:
            highestAttr = "NONE"
        if highestAttr.upper() == "CONFUSED":
            # avoid having too many times confused
            highestAttr = random.choice(confusedVariations)

        passportTexts[1] = " "+str(int(age))+"     "+sex
        passportTexts[3] = highestAttr
    except:
      print "error parsing data", sys.exc_info()[0]
      
    try:
        api_url = "https://api-us.faceplusplus.com/facepp/v3/detect"
        latestImagePath = max(glob.iglob('/home/pi/SensibleData/images/*.jpg'), key=os.path.getctime)
        fileToAnalyze = {'image_file': open(latestImagePath, 'rb')}
        data = {'api_key':'QY8OehSk-uGzRMvNiDpemlxkyr1PJI8t', 'api_secret':'M_5iW6pD0x_wf6rFckPuVaeByXdecyu7', 'return_attributes':'beauty,emotion,ethnicity,skinstatus,age,gender'}
        print "Trying to get Faceplusplus Analysis"
        r = requests.post(api_url, params=data, files=fileToAnalyze)
        print r
        jsondata =  r.json()
        # jsondata = {u'time_used': 1418, u'image_id': u'tD6dhWYeI/7Paq3XDxIVbg==', u'faces': [{u'attributes': {u'emotion': {u'neutral': 99.923, u'sadness': 0.001, u'disgust': 0.001, u'anger': 0.001, u'surprise': 0.059, u'fear': 0.016, u'happiness': 0.001}, u'beauty': {u'female_score': 70.965, u'male_score': 71.001}, u'gender': {u'value': u'Male'}, u'age': {u'value': 34}, u'skinstatus': {u'health': 24.239, u'stain': 3.233, u'acne': 1.918, u'dark_circle': 8.156}, u'ethnicity': {u'value': u'Black'}}, u'face_token': u'8626ef25346585288ae25a5671be819a', u'face_rectangle': {u'width': 535, u'top': 368, u'height': 535, u'left': 237}}], u'request_id': u'1524045332,eebeacc0-95b3-4e3f-8a7b-37cefa8a3a9b'}

        print "Got it"
        print jsondata
        firstFace = jsondata['faces'][0]['attributes']
        if firstFace["gender"]=="Male":
          sex = "M"
          beauty = firstFace["beauty"]["male_score"]
        else:
          sex = "F"
          beauty = firstFace["beauty"]["female_score"]
          
        passportTexts[2] = " "+str(int(beauty))
    except:
      print "error parsing data", sys.exc_info()[0]

    print passportTexts[1]
    print passportTexts[2]
    print passportTexts[3]
      


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

    # sendXY(INKPOS_X,INKPOS_Y)
    time.sleep(1)
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
            time.sleep(0.3)
            if (letter==" "):
                makeSpace()
            else:
                if(letter=="Y"):
                    letterUnicodeIndex=73
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
                nextStep = int(posInAlphabet*stepsPerLetter)
                # due to unprecise stepper that says it is 1/64 but is not really I add some steps
                #stepsToAdd = posInAlphabet/3
                #nextStep = nextStep+stepsToAdd
                if IS_WHEEL_INVERTED:
                    nextStep = -nextStep
                stepsToTake = (nextStep - currentStep)
                # if stepsToTake<0:
                #     stepsToTake=stepsToTake+2038
                gotoInkXY()
                sendRotation(stepsToTake)
                currentStep = nextStep
                zDownAndUpInk()
                time.sleep(0.2)
                print 'Stepped to '+letter+', '+str(stepsToTake)+' steps'
                gotoLetterXY()
                zDownAndUpStamp()
                # time.s(0.5)
                print 'got ink'
                print 'letter stamped'

        letterIndex = 1
        lineNr = lineNr+1

    # time.s(0.3)
    sendXY(MIN_X,MAX_Y)
    sendZ(Z_UP_POS)
    #stepsToZero = fullturnSteps-currentStep
    stepsToZero = -currentStep
    sendRotation(stepsToZero)
    currentStep = 0
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

def turnOnFingerprintLED():
    fps =  FPS.FPS_GT511C3(device_name='/dev/ttyAMA0',baud=9600,timeout=3,is_com=False)
    time.sleep(3)
    fps.SetLED(True)
    time.sleep(1)
    fps.Close()

def saveMailAddress(addressString):
    config = ConfigObj('/home/pi/SensibleData/latestMailAdr.cfg')
    newAddress = parseaddr(addressString)
    senderName = addressString.split("<")[0]
    print config['address']
    config['address'] = newAddress[1]
    config['name'] = senderName.rstrip()
    config.write()

def resetPositions():
    global currentX,currentY,currentZ,MIN_X,MIN_Y,MAX_Z,letterIndex,lineNr
    currentX = MIN_X
    currentY = MIN_Y
    currentZ = MAX_Z
    letterIndex = 1
    lineNr = 0

if __name__ == '__main__':
    while True:
        try:
            g = gmail.login("sensibledata1@gmail.com", "verysensible")
            unread = g.inbox().mail(unread=True)
            print unread
            if unread:
                # None
                unread[0].fetch()
                sender = unread[0].fr
                # senderNormalized = unicodedata.normalize('NFKD', sender).encode('ascii', 'ignore')
                # senderSubstring = senderNormalized[:8]
                senderSubstring = sender[:8]
                # remove special chars from string
                senderSubstringCleaned = re.sub('[^ a-zA-Z0-9]', '', senderSubstring)
                passportTexts[0] = senderSubstringCleaned.upper()
                print "NAME: "+passportTexts[0]
                unread[0].read()
                #uploadLatestImg()
                getFaceAnalysis()
                launchStamp()
                #uploadAnalyzedImg()
                turnOnFingerprintLED()
                saveMailAddress(sender)
                resetPositions()

            time.sleep(4)
            g.logout()
        except:
            pass
