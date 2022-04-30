#!/bin/bash

while :
do
  date
  echo "Start Loop"
  python3 ebusd2influxdb.py
  RET=$?
  if [ ${RET} -ne 0 ]; then
    echo "Exit status not 0"
    echo "retry in 10 s"
    sleep 10
  else
    date
    echo "Sleep 10 mins"
    sleep 600
  fi
done
