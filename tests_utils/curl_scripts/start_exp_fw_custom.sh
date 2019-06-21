#! /bin/bash -x

curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/exp/start/123/test \
    -F "firmware=@$1"; echo
