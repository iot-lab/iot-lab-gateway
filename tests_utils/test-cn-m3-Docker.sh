#! /bin/bash
#
# Test script for the following scenario
# - Docker container  attached to a standalone M3 OpenNode and standalone M3 ControlNode
# - The ControlNode board's FTDI eeprom has been set with the name ControlNode (using the IotLab ftdi-eeprom-config tool)

user='test'
experiment='123'
host=$(cat /tmp/cfg_dir/hostname)

# Experiment profile (sniffer) and firmware
profile="../gateway_code/tests/profiles/radio_sniffer_3.json"
firmware="../gateway_code/static/m3_autotest.elf"

# Start the gateway server and store the container name
xterm -e "cd ..; BOARD=m3 CONTROL_NODE_TYPE=iotlabm3 make run" &
echo 'Wait fo the server to start and press enter when ready'
read
gateway_container_name=$(docker ps -f 'ancestor=iot-lab-gateway' --format "{{.Names}}")

# Auto tests
#curl -X PUT http://localhost:8080/autotest/blink


# Launch experiments
echo "Submitting experiment"
curl -X POST -H "Content-Type: multipart/form-data" "http://localhost:8080/exp/start/$experiment/$user" -F "firmware=@$firmware" -F "profile=@$profile"; echo
echo 'do a netcat on localhost 20000 and send some data'

# Generate some radio to traffic using the control node
echo 'Sending some data'
for i in {1..5}; do  echo 'radio_ping_pong 11 3dBm' | nc -N localhost 20000; sleep 1; done

# Stop experiment
echo 'Stopping experiment'
curl -X DELETE  http://localhost:8080/exp/stop

# Check output OML file on the container
output_file="/tmp/exp_dir/sniffer/$(echo $host | tr '-' '_').oml"
echo "Content of the sniffer output from the gatweay container ($output_file)"
cat $output_file

echo 'Type enter to kill the servel'
read
# Kill the server
docker kill $gateway_container_name
