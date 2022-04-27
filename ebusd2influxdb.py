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
ebusd_host=os.getenv('EBUSD_HOST', "localhost")
ebusd_port=os.getenv('EBUSD_PORT', "")
ebusd_circuit=os.getenv('EBUSD_CIRCUIT', "")

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

    
# test if up
if pingTest(ebusd_host):
    print ("ping OK")
else:
    print ("ping NOK")
    quit(1)

# get eBUSd JSON via HTTP interface
#data/bai/?required
url="http://"+ebusd_host+":"+str(ebusd_port)+"/data/"+ebusd_circuit+"/?required"

try:
    raw = requests.get(url, timeout=4)
except requests.exceptions.Timeout as e:
    if debug:
        print ("eBUSd HTTP:",e)

if raw.status_code == requests.codes.ok:
    if debug:
        print ("eBUSd HTTP: OK ["+str(raw.status_code)+"]")
    dsList = raw.json()
    if debug and showraw:
        print ("eBUSd HTTP:")
        print (json.dumps(dsList,indent=4))
else:
    if debug:
        print ("eBUSd HTTP: NOK")




senddata={}
senddata["measurement"]="heating"
senddata["tags"]={}
senddata["tags"]["origin"]="eBUSd"
senddata["tags"]["source"]="docker ebusd-influxdb2"
senddata["fields"]={}

# pass info
global i
i = 0
for key in dsList["bai"]["messages"]:
    print ( key )
    name = dsList["bai"]["messages"][key]["name"]
    time = dsList["bai"]["messages"][key]["lastup"]
    print ( str(i)+": name = "+name+" time = "+str(time) )
    for field in dsList["bai"]["messages"][key]["fields"]:
        print ( dsList["bai"]["messages"][key]["fields"][field] )

    #    field=key[i]["fields"]
    #    value=key[i]["fields"][field]["value"]

    #print ( "name: "+name+" time= "+time+" field= "+field+" value"+value)
    i += 1

    # senddata["tags"]["host"]=name

    # if key2['nukiId'] == nukiID:
    #     rssi=key2['rssi']
    #     signal=( rssi + 100 )*2.0

    #     senddata["fields"]["percent"]=signal
    #     senddata["fields"]["rssi"]=rssi
    #     write_influxdb()


quit()

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
