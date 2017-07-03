#!/bin/bash

echo $BOARD_TYPE > /var/local/config/board_type
echo $CONTROL_NODE_TYPE > /var/local/config/control_node_type
echo $HOSTNAME > /var/local/config/hostname


# Start the first process
python /home/iot-lab-gateway/gateway_code/rest_server.py 0.0.0.0 8080
