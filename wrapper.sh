#!/bin/bash

echo $BOARD_TYPE > /var/local/config/board_type
echo $CONTROL_NODE_TYPE > /var/local/config/control_node_type
echo $HOSTNAME > /var/local/config/hostname


# Start the first process
python /home/iot-lab-gateway/gateway_code/rest_server.py 0.0.0.0 8080 &

status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start gateway server daemon: $status"
  exit $status
fi


# Naive check runs checks once a minute to see if either of the processes exited.
# This illustrates part of the heavy lifting you need to do if you want to run
# more than one service in a container. The container will exit with an error
# if it detects that either of the processes has exited.
# Otherwise it will loop forever, waking up every 60 seconds

while /bin/true; do
  PROCESS_STATUS=$(ps aux |grep -q home/iot-lab-gateway/gateway_code/rest_server.py |grep -v grep)
  # If the greps above find anything, they will exit with 0 status
  # If they are not both 0, then something is wrong
  if [ $PROCESS_STATUS ]; then
    echo "Rest server has exited."
    exit -1
  fi
  sleep 60
done
