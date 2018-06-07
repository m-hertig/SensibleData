# SensibleData

# Install
Dependencies
run install.sh
- aws cli
- aws configure -> add aws credentials

# Run at startup
tap `sudo crontab -e` in terminal
add the following line to crontab
```@reboot /home/pi/SensibleData/startSensibleData.sh```
