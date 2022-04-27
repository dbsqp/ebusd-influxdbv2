#!/bin/bash

while :
do
  date
  echo "Start Loop"
  python3 ebusd2influxdb.py
  RET=$?
  if [ ${RET} -ne 0 ];
  then
    echo "Exit status not 0"
    echo "Sleep 5 mins"
    sleep 300
  fi
  date
  echo "Sleep 10 mins"
  sleep 600
done
