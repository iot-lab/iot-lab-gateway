#! /bin/bash -x


curl -X POST -H "Content-Type: multipart/form-data" http://gateway:8080/exp/start/123/clochette -F "firmware=@simple_idle.elf" -F "profile=@profile.json"; echo
