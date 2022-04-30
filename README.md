# ebusd-influxdbv2
Docker image to fetch data from eBUSd HTTP interface and push it to an InfluxDBv2 bucket. 

## eBUSd Setup
1. Setup physical connection and interface. The specific interface used was:
- https://fromeijn.nl/connected-vaillant-to-home-assistant/
- https://gitlab.com/fromeijn/ebuzzz-adapter
2. Install USB serial drivers for Synology NAS under DSM 7
- install, load, setup load at startup script
2. Setup eBUSd docker container:
- https://registry.hub.docker.com/r/john30/ebusd/
- https://github.com/john30/ebusd
3. Configure docker container to allow access to serial USB device
- create container, stop, export json, edit json to add device, import
6. Test using docker bash terminal using ebusctl:
- ebusctl info, ebusdctl find
- note circuit name(s) to be monitored
 
See eBUSd for more information https://github.com/john30/ebusd.

## InfluxDBv2 Setup
Setup InfluxDBv2, create bucket and create a token with write permissions for bucket.

## Docker Setup
https://hub.docker.com/repository/docker/dbsqp/ebusd-influxdbv2
```
$ docker run -d \
 -e EBUSD_IP="<eBUSd server>" \
 -e EBUSD_PORT="<port>" \
 -e EBUSD_CIRCUIT_LIST="['<#1>','<#2>',...]" \
 -e EBUSD_IGNORE_LIST ="['<ignore1>','<ignore2>',...]" \
 -e EBUSD_OVERRIDE_LIST="[['<old1>','<new1>'],['old2','new2'],...]" \
 -e INFLUXDB2_HOST="<INFLUXDBv2 SERVER>" \
 -e INFLUXDB2_PORT="8086" \
 -e INFLUXDB2_ORG="Home" \
 -e INFLUXDB2_TOKEN="" \
 -e INFLUXDB2_BUCKET="Staging" \
 --name "Influx-eBUSd" \
dbsqp/ebusd-influxdbv2:latest
```

## Debug
To report out further details in the log enable debug:
```
 -e DEBUG="TRUE"
```

## Todo
-Pass multi field items.

