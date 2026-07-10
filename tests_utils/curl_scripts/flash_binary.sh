#! /bin/bash -x

# tries to flash a binary firmware with default offset 0x0 on the open node

curl -X POST  -H "Content-Type: multipart/form-data" -F "firmware=@$1" http://localhost:8080/open/flash?binary=1 ; echo
