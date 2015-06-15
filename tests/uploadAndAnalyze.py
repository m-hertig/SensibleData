import os, glob, ftplib
session = ftplib.FTP('109.239.61.126','336054-90-sensibleData','JRWZr3EH&&cC')
latestImagePath = max(glob.iglob('/home/pi/SensibleData/images/*.jpg'), key=os.path.getctime)
latestImageFilename = os.path.basename(latestImagePath)
file = open(latestImagePath,'rb')               # file to send
session.storbinary('STOR imageToAnalyze.jpg', file)     # send the file
file.close()                                    # close file and FTP
session.quit()
