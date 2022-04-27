#!/usr/bin/python3
# encoding=utf-8

from pytz import timezone
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import os
import sys
import requests
import subprocess
import platform


# function ping test
def pingTest(pingHost):
    try:
        output = subprocess.check_output("ping -{} 1 {}".format('n' if platform.system().lower()=="windows" else 'c', pingHost), shell=True)#    except Exception as e:
    except Exception as e:
        return False
    return True


# debug enviroment variables
showraw = False
debug_str=os.getenv("DEBUG", None)
if debug_str is not None:
    debug = debug_str.lower() == "true"
else:
    debug = False


# Nuki envionment variables
nuki_api_token=os.getenv('NUKI_WEB_API_TOKEN', "")
nuki_bridge_ip=os.getenv('NUKI_BRIDGE_IP', "")
nuki_bridge_token=os.getenv('NUKI_BRIDGE_TOKEN', "")

# influxDBv2 envionment variables
influxdb2_host=os.getenv('INFLUXDB2_HOST', "localhost")
influxdb2_port=int(os.getenv('INFLUXDB2_PORT', "8086"))
influxdb2_org=os.getenv('INFLUXDB2_ORG', "Home")
influxdb2_token=os.getenv('INFLUXDB2_TOKEN', "")
influxdb2_bucket=os.getenv('INFLUXDB2_BUCKET', "DEV")

# hard encoded envionment varables for testing
if os.path.exists('private-ebusd.py'):
    print("  incl: private-ebusd.py")
    exec(compile(source=open('private-ebusd.py').read(), filename='private-ebusd.py', mode='exec'))
    debug = True


# report debug status
if debug:
    print ( " debug: TRUE" )
else:
    print ( " debug: FALSE" )


# influxDBv2
influxdb2_url="http://" + influxdb2_host + ":" + str(influxdb2_port)
if debug:
    print ( "influx: "+influxdb2_bucket+" at "+influxdb2_url )

client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org)
write_api = client.write_api(write_options=SYNCHRONOUS)

def write_influxdb():
    if debug:
        print ("INFLUX: "+influxdb2_bucket)
        print (json.dumps(senddata,indent=4))
    write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])



# get eBUSd JSON via HTTP interface
if nukiBridge:
    url="http://"+nuki_bridge_ip+":8080/list&token="+nuki_bridge_token

    try:
        raw = requests.get(url, timeout=4)
    except requests.exceptions.Timeout as e:
        if debug:
            print ("BL API:",e)

    if raw.status_code == requests.codes.ok:
        if debug:
            print ("BL API: OK ["+str(raw.status_code)+"]")
        dsList = raw.json()
        if debug and showraw:
            print ("BL RAW:")
            print (json.dumps(dsList,indent=4))
    else:
        if debug:
            print ("BL API: NOK")

    url="http://"+nuki_bridge_ip+":8080/info&token="+nuki_bridge_token
    try:
        raw = requests.get(url, timeout=4)
    except requests.exceptions.Timeout as e:
        if debug:
            print ("BI API:",e)

    if raw.status_code == requests.codes.ok:
        if debug:
            print ("BI API: OK ["+str(raw.status_code)+"]")
        dsInfo = raw.json()
        if debug and showraw:
            print ("BI RAW:")
            print (json.dumps(dsInfo,indent=4))
    else:
        if debug:
            print ("BI API: NOK")


    senddata={}
    senddata["measurement"]="signal"
    senddata["tags"]={}
    senddata["tags"]["origin"]="Nuki"
    senddata["tags"]["source"]="docker nuki-influxdb2"
    senddata["fields"]={}

    # pass info
    for key in dsList:
        name=key['name']
        nukiID=key['nukiId']

        senddata["tags"]["host"]=name

        for key2 in dsInfo['scanResults']:
            if key2['nukiId'] == nukiID:
                rssi=key2['rssi']
                signal=( rssi + 100 )*2.0

                senddata["fields"]["percent"]=signal
                senddata["fields"]["rssi"]=rssi
                write_influxdb()




# pass smartlock devices
for key in devList:
    name=key['name']
    smartlockID=key['smartlockId']
    stateID=key['state']['state']
    triggerID=key['state']['trigger']

    if   triggerID == 0: trigger="proximity"
    elif triggerID == 1: trigger="manual"
    elif triggerID == 2: trigger="button"
    elif triggerID == 3: trigger="automatic"
    elif triggerID == 6: trigger="continious"
    else:                trigger="other"

    if key['type'] == 2:
        if   stateID == 1: state="online"
        elif stateID == 3: state="ring-to-open"
        elif stateID == 5: state="open"
        elif stateID == 7: state="opening"
        else:              state="other"
    else:
        if   stateID == 1: state="locked"
        elif stateID == 2: state="unlocking"
        elif stateID == 3: state="unlocked"
        elif stateID == 4: state="locking"
        elif stateID == 5: state="unlatched"
        elif stateID == 6: state="lock-n-go"
        elif stateID == 7: state="unlatching"
        else:              state="other"

    senddata={}
    senddata["measurement"]="lock"
    senddata["tags"]={}
    senddata["tags"]["origin"]="Nuki"
    senddata["tags"]["source"]="docker nuki-influxdb2"
    senddata["tags"]["host"]=name
    senddata["fields"]={}
    senddata["fields"]["trigger"]=trigger
    senddata["fields"]["state"]=state
    write_influxdb()
    del senddata["fields"]["trigger"]
    del senddata["fields"]["state"]

    if key['type'] == 2:
        if key['state']['batteryCritical'] == "true":
            battery=10
        else:
            battery=100
        battery=float(round(battery,2))
        senddata["measurement"]="battery"
        senddata["fields"]["percent"]=battery
        write_influxdb()

    else:
        if 'batteryCharge' in key['state']:
            battery=key['state']['batteryCharge']
            battery=float(round(battery,2))

            senddata["measurement"]="battery"
            senddata["fields"]["percent"]=battery
            write_influxdb()

    if 'percent' in senddata["fields"]:
        del senddata["fields"]["percent"]

    for logEntry in logList:
        if logEntry['smartlockId'] == smartlockID:
            senddata["measurement"]="lock"
            senddata["time"]=logEntry['date']

            stateID=logEntry['state']

            if logEntry['deviceType'] == 2:
                if   stateID == 1: state="online"
                elif stateID == 3: state="ring-to-open"
                elif stateID == 5: state="open"
                elif stateID == 7: state="opening"
                else:              state="other"
            else:
                if   stateID == 1: state="locked"
                elif stateID == 2: state="unlocking"
                elif stateID == 3: state="unlocked"
                elif stateID == 4: state="locking"
                elif stateID == 5: state="unlatched"
                elif stateID == 6: state="lock-n-go"
                elif stateID == 7: state="unlatching"
                else:              state="other"

            triggerID=logEntry['trigger']

            if   triggerID == 0: trigger="proximity"
            elif triggerID == 1: trigger="manual"
            elif triggerID == 2: trigger="button"
            elif triggerID == 3: trigger="automatic"
            elif triggerID == 6: trigger="continious"
            else:                trigger="other"

            who=logEntry['name']

            if not who:
                who="other"

            senddata["tags"]["who"]=who
            senddata["fields"]["trigger"]=trigger
            senddata["fields"]["state"]=state
            write_influxdb()
