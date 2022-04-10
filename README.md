# nuki-influxdbv2
Fetch data from Nuki bridge via API and push to influxdb v2 bucket.

## Nuki Accessories
- Enable API on Nuki Bridge
- Get API token
- Create list of opener ids: ['ID1','ID2', ...]
- Create list of lock ids: ['ID1','ID2', ...]


## InfluxDBv2 Setup
Setup InfluxDBv2, create bucket and create a token with write permissions for bucket.

## Docker Setup
```
$ docker run -d \
 -e NUKI_BRIDGE="<IP>" \
 -e NUKI_TOKEN="<apikey>" \
 -e NUKI_OPENER_LIST="['',['<id>',...]" \
 -e NUKI_LOCK_LIST="['',['<id>',...]" \
 -e INFLUXDB2_HOST="<INFLUXDBv2 SERVER>" \
 -e INFLUXDB2_PORT="8086" \
 -e INFLUXDB2_ORG="Home" \
 -e INFLUXDB2_TOKEN="" \
 -e INFLUXDB2_BUCKET="Staging" \
 --name "Influx-Nuki" \
dbsqp/nuki-influxdbv2:latest
```

## Debug
To report out further details in the log enable debug:
```
 -e DEBUG="TRUE"
```
