#! /bin/bash

LOGFILE="/tmp/iot-lab-gateway/gateway-server.log"

while ! test -f ${LOGFILE}
do
    sleep 1
done


tail -f /tmp/iot-lab-gateway/gateway-server.log /var/log/messages
