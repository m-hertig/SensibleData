import os
import glob
newest = max(glob.iglob('/home/pi/SensibleData/images/*.jpg'), key=os.path.getctime)
print newest