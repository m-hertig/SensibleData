import RPi.GPIO as GPIO
from time import sleep
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(4, GPIO.RISING)
magnetCounter = 0
def magnetDetected(infos):
	global magnetCounter
	magnetCounter = magnetCounter+1
	print 'MAGNET! '+str(magnetCounter)

GPIO.add_event_callback(4, magnetDetected)
while True:
	pass
