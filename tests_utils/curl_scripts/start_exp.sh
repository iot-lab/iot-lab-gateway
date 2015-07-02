#! /bin/bash -x


curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/exp/start/123/test -F "firmware=@simple_idle.elf" -F "profile=@consumption.json"; echo
