#! /bin/bash -x

# start an experiment (id 123, user named test), with the simple_idle firmware and the consumption.json monitoring profile


curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/exp/start/123/test -F "firmware=@simple_idle.elf" -F "profile=@consumption.json"; echo
