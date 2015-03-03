#! /bin/bash -x

if [[ "x" == "x$1" ]]
then
        IP_ADDR=192.168.1.5
else
        IP_ADDR=$1
fi

curl -X PUT http://$IP_ADDR:8080/autotest/blink?channel=22; echo

date
