import time, os
while True:
	os.system("/home/pi/SensibleData/dropbox_uploader.sh -q -s download /images/  /home/pi/SensibleData/")
	time.sleep(2)