#! /bin/bash -x

# tries to flash the serial_echo.elf firmware on the open node

curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/open/flash -F "firmware=@serial_echo.elf"; echo
