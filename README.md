# nuki-influxdbv2
Docker image to fetch data from Nuki Web API and push to influxdb v2 bucket.
https://developer.nuki.io/page/nuki-web-api-1-4/3

Optionally also pulls signal strengths from Nuki Bridge on local LAN.

## Nuki Accessories
1. Go to https://web.nuki.io/
2. Generate API Token with scope:
- View devices
- View activity logs
3. get API token

Optional
- Setup token for Nuki Bridge

## InfluxDBv2 Setup
Setup InfluxDBv2, create bucket and create a token with write permissions for bucket.

## Docker Setup
https://hub.docker.com/repository/docker/dbsqp/nuki-influxdbv2
```
$ docker run -d \
 -e NUKI_WEB_API_TOKEN="<web-api-token>" \
 -e NUKI_BRIDGE_IP="<ip-address-of-bridge>" \
 -e NUKI_BRIDGE_TOKEN="<bridge-api-token>" \
 -e INFLUXDB2_HOST="<INFLUXDBv2 SERVER>" \
 -e INFLUXDB2_PORT="8086" \
 -e INFLUXDB2_ORG="Home" \
 -e INFLUXDB2_TOKEN="" \
 -e INFLUXDB2_BUCKET="Staging" \
 --name "Influx-Nuki" \
dbsqp/nuki-influxdbv2:latest
```
Note NUKI_BRIDGE_IP and NUKI_BRIDGE_TOKEN are optional.

## Debug
To report out further details in the log enable debug:
```
 -e DEBUG="TRUE"
```
