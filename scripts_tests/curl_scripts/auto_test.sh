#! /bin/bash -x

curl -X PUT http://localhost:8080/status/blink?channel=22; echo
