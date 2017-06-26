#!/bin/sh

OPT_DIR=""
BOARD_TYPE="firefly"
CONTROL_NODE_TYPE="no"
HOSTNAME="custom-123"

while getopts "c:b:h:" opt ; do
case $opt in
    b) BOARD_TYPE=$OPTARG; shift 2;;
    h) HOSTNAME=$OPTARG; shift 2 ;;
    c) CONTROL_NODE_TYPE=$OPTARG; shift 2 ;;

esac
done

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
  -e BOARD_TYPE=$BOARD_TYPE \
  -e CONTROL_NODE_TYPE=$CONTROL_NODE_TYPE \
  -e HOSTNAME=$HOSTNAME \
  -p 8080:8080 \
  -p 20000:20000 \
  --name "gateway_test" \
  --privileged \
  -v /dev:/dev \
  -d \
  iot_gateway
