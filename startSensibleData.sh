# Start all sensible data scripts
# tap 'sudo crontab -e & put the following line in there'
# @reboot /home/pi/SensibleData/startSensibleData.sh

/usr/bin/python /home/pi/SensibleData/webapp/app.py &
/usr/bin/python /home/pi/SensibleData/PiccoloStampSimple.py &
/usr/bin/python /home/pi/SensibleData/PiccoloStampRekognition.py &
/usr/local/bin/watchmedo shell-command --patterns="*.jpg" --command='flock -n /home/pi/SensibleData/drawportrait.lockfile -c "/usr/bin/python /home/pi/SensibleData/DrawPortrait.py"'  /home/pi/SensibleData/images/ &
