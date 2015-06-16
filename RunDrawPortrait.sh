#!/bin/bash

#check if abc is running
if pgrep DrawPortrait.py >/dev/null 2>&1
  then
     echo 'DrawPortrait.py already running'
  else
  		echo 'Start DrawPortrait.py'
     /home/pi/SensibleData/DrawPortrait.py &
fi