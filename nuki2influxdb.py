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
nuki_bridge=os.getenv('NUKI_BRIDGE', "")
nuki_token=os.getenv('NUKI_TOKEN', "")

# influxDBv2 envionment variables
influxdb2_host=os.getenv('INFLUXDB2_HOST', "localhost")
influxdb2_port=int(os.getenv('INFLUXDB2_PORT', "8086"))
influxdb2_org=os.getenv('INFLUXDB2_ORG', "Home")
influxdb2_token=os.getenv('INFLUXDB2_TOKEN', "token")
influxdb2_bucket=os.getenv('INFLUXDB2_BUCKET', "DEV")

# hard encoded envionment varables for testing

# report debug status
if debug:
	print ( " debug: TRUE" )
else:
	print ( " debug: FALSE" )

# influxDBv2
influxdb2_url="http://" + influxdb2_host + ":" + str(influxdb2_port)
if debug:
	print ( "influx: "+influxdb2_url )
	print ( "bucket: "+influxdb2_bucket )

client = InfluxDBClient(url=influxdb2_url, token=influxdb2_token, org=influxdb2_org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# set date
time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ") 

# test if bridge responde to ping
if pingTest(nuki_bridge):
	if debug:
		print ("  PING: OK")
else:
	if debug:
		print ("  PING: NOK")
#	continue

# get API
url="http://"+nuki_bridge+":8080/list&token="+nuki_token
try:
	raw = requests.get(url, timeout=4)
except requests.exceptions.Timeout as e: 
	if debug:
		print ("   API:",e)
#	continue

if raw.status_code == requests.codes.ok:
	if debug:
		print ("   API: OK ["+str(raw.status_code)+"]")
	dsList = raw.json()
	if debug and showraw:
		print ("   RAW:")
		print (json.dumps(dsList,indent=4))
else:
	if debug:
		print ("   API: NOK")
#	continue

url="http://"+nuki_bridge+":8080/info&token="+nuki_token
try:
	raw = requests.get(url, timeout=4)
except requests.exceptions.Timeout as e:
	if debug:
		print ("   API:",e)
#	continue

if raw.status_code == requests.codes.ok:
	if debug:
		print ("   API: OK ["+str(raw.status_code)+"]")
	dsInfo = raw.json()
	if debug and showraw:
		print ("   RAW:")
		print (json.dumps(dsInfo,indent=4))
else:
	if debug:
		print ("   API: NOK")
#	continue

       
# pass info
for key in dsList:
	name=key['name']
	nukiID=key['nukiId']
	state=key['lastKnownState']['stateName']

	senddata={}
	senddata["measurement"]="lock"
	senddata["tags"]={}
	senddata["tags"]["origin"]="Nuki"
	senddata["tags"]["source"]="docker nuki-influxdb2"
	senddata["tags"]["host"]=name
	senddata["fields"]={}
	senddata["fields"]["state"]=state

	if debug:
		print ("INFLUX: "+influxdb2_bucket)
		print (json.dumps(senddata,indent=4))
		write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])

	if key['lastKnownState']['batteryCritical'] == "true":		battery=10
	else:
		battery=100
	battery=float(round(battery,1))


	senddata={}
	senddata["measurement"]="battery"
	senddata["tags"]={}
	senddata["tags"]["origin"]="Nuki"
	senddata["tags"]["source"]="docker nuki-influxdb2"
	senddata["tags"]["host"]=name
	senddata["tags"]["type"]="critical"
	senddata["fields"]={}
	senddata["fields"]["percent"]=battery

	if debug:
		print ("INFLUX: "+influxdb2_bucket)
		print (json.dumps(senddata,indent=4))
		write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])


	if 'batteryChargeState' in key['lastKnownState']:
		battery=key['lastKnownState']['batteryChargeState']
		battery=float(round(battery,1))

		senddata={}
		senddata["measurement"]="battery"
		senddata["tags"]={}
		senddata["tags"]["origin"]="Nuki"
		senddata["tags"]["source"]="docker nuki-influxdb2"
		senddata["tags"]["host"]=name
		senddata["tags"]["type"]="charge"
		senddata["fields"]={}
		senddata["fields"]["percent"]=battery

		if debug:
			print ("INFLUX: "+influxdb2_bucket)
			print (json.dumps(senddata,indent=4))
			write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])

	for key2 in dsInfo['scanResults']:
		if key2['nukiId'] == nukiID:
			rssi=key2['rssi']
			signal=( rssi + 100 )*2.0

	senddata={}
	senddata["measurement"]="signal"
	senddata["tags"]={}
	senddata["tags"]["origin"]="Nuki"
	senddata["tags"]["source"]="docker nuki-influxdb2"
	senddata["tags"]["host"]=name
	senddata["fields"]={}
	senddata["fields"]["percent"]=signal
	senddata["fields"]["rssi"]=rssi

	if debug:
		print ("INFLUX: "+influxdb2_bucket)
		print (json.dumps(senddata,indent=4))
		write_api.write(bucket=influxdb2_bucket, org=influxdb2_org, record=[senddata])
