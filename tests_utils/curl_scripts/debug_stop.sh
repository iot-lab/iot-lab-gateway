#! /bin/bash -x

# stop debugging the open node

curl -X PUT http://localhost:8080/open/debug/stop; echo
