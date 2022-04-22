# nuki-influxdbv2
Docker image to fetch data from Nuki bridge via API and push to influxdb v2 bucket.

## Nuki Accessories
- Enable API on Nuki Bridge
- Get API token

## InfluxDBv2 Setup
Setup InfluxDBv2, create bucket and create a token with write permissions for bucket.

## Docker Setup
https://hub.docker.com/repository/docker/dbsqp/nuki-influxdbv2
```
$ docker run -d \
 -e NUKI_BRIDGE="<IP>" \
 -e NUKI_TOKEN="<apikey>" \
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
