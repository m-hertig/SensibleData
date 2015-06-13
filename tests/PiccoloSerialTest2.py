import serial, struct
import time
ser = serial.Serial('/dev/ttyACM0', 115200)
# ser.write('P')
ser.write('C')
ser.read(6)
ser.flushInput()
# ser.write(struct.pack('i',0))
# ser.write(struct.pack('i',0))
# ser.write(struct.pack('i',2500))
# ser.write(';')
# time.sleep(0.1)

while  True:
	ser.write('P')
	ser.write(struct.pack('i',2500))
	ser.write(struct.pack('i',2500))
	ser.write(struct.pack('i',2500))
	ser.write(';')
	ser.read(3)
	ser.write('P')
	ser.write(struct.pack('i',-2500))
	ser.write(struct.pack('i',-2500))
	ser.write(struct.pack('i',-2500))
	ser.write(';')
	ser.read(3)

	# while True:
	# 	ser.write('R')
	# 	ser.write(struct.pack('i',1839))
	# 	ser.write(';')
	# 	print(ser.read(3))
	# 	time.sleep(0.5)

ser.write('E')
time.sleep(1)
ser.flushInput()

