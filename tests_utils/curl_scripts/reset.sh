#! /bin/bash -x

# soft reset the node

curl -X PUT http://localhost:8080/open/reset; echo
