#! /bin/bash -x


curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/exp/start/123/clochette -F "firmware=@serial_echo.elf" -F "profile=@profile.json"; echo
