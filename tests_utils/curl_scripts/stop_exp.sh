#! /bin/bash -x

# stop the currently running experiment

curl -X DELETE http://localhost:8080/exp/stop ; echo
