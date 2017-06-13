#!/bin/sh

OPT_DIR=""
if [ ! -z $1 ] ; then
  if [ -d $1 ] ; then
    echo "$1 mounted as gateway_code repository\n"
    OPT_DIR="-v $1:/usr/local/lib/python2.7/dist-packages/gateway_code-2.4.0-py2.7-linux-x86_64.egg/gateway_code"
  else
    echo "Please use a valid path.\n"
    exit 0
  fi
fi
docker run \
  $OPT_DIR \
  --rm \
  -p 8080:8080 \
  -p 20000:20000 \
  --name "gateway_test" \
  --privileged \
  -v /dev:/dev \
  -d \
  iot_gateway
