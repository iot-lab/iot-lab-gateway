#! /bin/bash -x

# stop the open node

curl -X PUT http://localhost:8080/open/stop; echo
