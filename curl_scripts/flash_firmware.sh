#! /bin/bash -x

curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/open/flash -F "firmware=@serial_echo.elf"; echo
