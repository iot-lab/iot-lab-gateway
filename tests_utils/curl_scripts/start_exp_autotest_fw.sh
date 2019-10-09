#! /bin/bash -x

# start an autotest experiment with fox_autotest.elf, and monitoring consumption.elf


curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/exp/start/123/test -F "firmware=@/tmp/iot-lab-gateway/gateway_code/static/fox_autotest.elf" -F "profile=@consumption.json"; echo
