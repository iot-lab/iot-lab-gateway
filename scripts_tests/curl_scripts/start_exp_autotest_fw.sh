#! /bin/bash -x


mkdir -p ../../../clochette/.senslab/123/consumption
mkdir -p ../../../clochette/.senslab/123/radio

curl -X POST -H "Content-Type: multipart/form-data" http://gateway:8080/exp/start/123/clochette -F "firmware=@../../static/m3_autotest.elf" -F "profile=@consumption.json"; echo
