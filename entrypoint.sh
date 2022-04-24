#!/bin/bash

while :
do
  date
  echo "Start Loop"
  python3 nuki2influxdb.py
  RET=$?
  if [ ${RET} -ne 0 ];
  then
    echo "Exit status not 0"
    echo "Sleep 5 mins"
    sleep 300
  fi
  date
  echo "Sleep 30 mins"
  sleep 1800
done
