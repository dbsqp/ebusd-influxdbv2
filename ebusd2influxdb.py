#!/usr/bin/env python3
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
import time



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
ebusd_port=os.getenv('EBUSD_PORT', "8889")
ebusd_circuits_str=os.getenv('EBUSD_CIRCUIT_LIST', "[]")
ebusd_ignoreKeys_str=os.getenv('EBUSD_IGNORE_LIST', "[]")
ebusd_overideKeys_str=os.getenv('EBUSD_OVERRIDE_LIST', "()")

ebusd_circuits=eval(ebusd_circuits_str)
ebusd_ignoreKeys=eval(ebusd_ignoreKeys_str)
ebusd_overideKeys=eval(ebusd_overideKeys_str)

# influxDBv2 envionment variables
influxdb2_host=os.getenv('INFLUXDB2_HOST', "localhost")
influxdb2_port=int(os.getenv('INFLUXDB2_PORT', "8086"))
influxdb2_org=os.getenv('INFLUXDB2_ORG', "Home")
influxdb2_token=os.getenv('INFLUXDB2_TOKEN', "")
influxdb2_bucket=os.getenv('INFLUXDB2_BUCKET', "DEV")

# hard encoded envionment varables for testing
if os.path.exists('private-ebusd.py'):
    print("   incl: private-ebusd.py")
    exec(compile(source=open('private-ebusd.py').read(), filename='private-ebusd.py', mode='exec'))


# report debug status
if debug:
    print ( "  debug: TRUE" )
else:
    print ( "  debug: FALSE" )


# influxDBv2
influxdb2_url="http://" + influxdb2_host + ":" + str(influxdb2_port)
if debug:
    print ( " influx: "+influxdb2_bucket+" at "+influxdb2_url )

client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org)
write_api = client.write_api(write_options=SYNCHRONOUS)

def write_influxdb():
    if debug:
        print ("INFLUX: "+influxdb2_bucket)
        print (json.dumps(senddata,indent=4))
    write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])

    
# test if up
if pingTest(ebusd_host):
    print ("   ping: OK")
else:
    print ("   ping: NOK")
    quit(1)


# transpose overrides
ebusd_keyOverides=[[row[i] for row in ebusd_overideKeys] for i in range(len(ebusd_overideKeys[0]))]


# setup globals
senddata={}
senddata["measurement"]="heating"
senddata["tags"]={}
senddata["tags"]["origin"]="eBUSd"
senddata["tags"]["source"]="docker ebusd-influxdb2"
senddata["fields"]={}


# for each circuit
print ("polling:",ebusd_circuits)

for circuit in ebusd_circuits:
    print ("circuit:",circuit)
    senddata["tags"]["circuit"]=circuit

    # get JSON via HTTP interface ip:port/data/circuit/?required&maxage=60
    url="http://"+ebusd_host+":"+str(ebusd_port)+"/data/"+circuit+"/?required&maxage=60"
    
    if debug:
        print ( " url: "+url )

    try:
        raw = requests.get(url, timeout=4)
    except requests.exceptions.Timeout as e:
        print ("ER HTTP:",e)
        quit(1)

    if raw.status_code == requests.codes.ok:
        print ("   HTTP: OK ["+str(raw.status_code)+"]")
        dList = raw.json()
        if showraw:
            print ("   HTTP:")
            print (json.dumps(dList,indent=4))
    else:
        print ("ER  HTTP: NOK")


    # pass JSON
    if showraw:
        print ( "\nPassed JSON\n")

    global n, edited, valueList
    n = 0

    for key in dList[circuit]['messages']:
        edited = False
        valueList=[]

        print ( str(n).rjust(3,' '),'', end='' )

        if key in ebusd_ignoreKeys:
            print ( "-",key.rjust(30,' ') )
            n += 1
            continue
        for key2 in dList[circuit]['messages'][key]:
            if key2 == 'fields':
                fields = dList[circuit]['messages'][key]['fields']
                nFields = len(fields)
                for field in fields:
                    if nFields == 1:
                        value = dList[circuit]['messages'][key]['fields'][field]['value']
                    else:
                        valueList.append( dList[circuit]['messages'][key]['fields'][field]['value'] )

            if key2 == "name":
                name = dList[circuit]['messages'][key]['name']
                if name in ebusd_keyOverides[0]:
                    name = ebusd_keyOverides[1][ebusd_keyOverides[0].index(name)]
                    edited = True

            if key2 == "lastup":
                times = dList[circuit]['messages'][key]['lastup']

        timef = time.strftime("%Y-%m-%dT%H:%M:%S.00%z", time.localtime(times))
        timev = time.strftime("%a %d %H:%M:%S", time.localtime(times))

        senddata["tags"]['key']=key
        senddata["time"]=timef

        if nFields == 1:
            if not edited:
                print ( "u "+key.rjust(30,' ')+" = "+str(value).ljust(20,' ')+" "+str(timev), end='')
            else:
                print ( "e "+key.rjust(30,' ')+" >\n    u "+name.rjust(30,' ')+" = "+str(value).ljust(20,' ')+" "+str(timev), end='')

            senddata["fields"][name]=value
            write_influxdb()
            del senddata["fields"][name]
            print ( " >")
        else:
            print ( "x "+key.rjust(30,' ')+" "+str(nFields)+" "+str(valueList).ljust(20,' ')+" "+str(timev) )

        n += 1

quit(0)
