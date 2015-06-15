watchmedo shell-command --patterns="*.jpg" --command='flock -n /home/pi/SensibleData/drawportrait.lockfile -c "python /home/pi/SensibleData/DrawPortrait.py 400 ${watch_src_path}"'  /home/pi/SensibleData/images/


sudo /usr/local/bin/dbdownload -s Chargements\ appareil\ photo -t /home/pi/SensibleData/images -i 5 -a /home/pi/.dbdownload.cache -x "flock -n /home/pi/SensibleData/drawportrait.lockfile -c /home/pi/SensibleData/DrawPortrait.py"