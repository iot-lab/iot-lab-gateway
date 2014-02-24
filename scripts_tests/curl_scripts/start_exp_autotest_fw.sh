#! /bin/bash -x


ssh gateway 'rm   -rf /iotlab/users/clochette/.senslab/123/
             mkdir -p /iotlab/users/clochette/.senslab/123/consumption
             mkdir -p /iotlab/users/clochette/.senslab/123/radio'

curl -X POST -H "Content-Type: multipart/form-data" http://gateway:8080/exp/start/123/clochette -F "firmware=@../../static/m3_autotest.elf" -F "profile=@consumption.json"; echo
