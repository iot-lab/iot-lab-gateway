#! /bin/bash -x

# start an experiment (id 123, user named test), with the given firmware
# example:
#  ./start_exp_fw.sh <path-to-firmware.elf>


curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/exp/start/123/test \
    -F "firmware=@$1" -F "profile=@consumption.json"; echo
