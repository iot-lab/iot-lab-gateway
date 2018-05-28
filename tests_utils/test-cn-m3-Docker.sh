#! /bin/bash
#
# Test script for the following scenario
# - Docker container named 'gateway_test' attached to a standalone M3 OpenNode and standalone M3 ControlNode
# - The ControlNode board's FTDI eeprom has been set with the name ControlNode (using the IotLab ftdi-eeprom-config tool)

# Experiment profile (sniffer) and firmware
profile="../gateway_code/tests/profiles/radio_sniffer_3.json"
firmware="../gateway_code/static/m3_autotest.elf"

# Mocked user workspace and experiment folders (usually mounted by nfs)
# here, they are created in the (alreadyà running container
user="test"
experiment="123"
host=$(cat /tmp/cfg_dir/hostname | tr '-' '_')
WORKDIR="/iotlab/users/$user/.iot-lab/$experiment"
FOLDERS="consumption radio event sniffer log"

CMD="for f in $FOLDERS; "
CMD+='do rm -rf $f; mkdir $f; done'
docker exec -w '/' gateway_test "mkdir" "-p" "-m0666" "$WORKDIR" 
docker exec -w "$WORKDIR" gateway_test '/bin/bash' '-c' "$CMD"
docker exec gateway_test 'chown' '-R' 'www-data' "$WORKDIR"
docker exec gateway_test 'chgrp' '-R' 'www-data' "$WORKDIR"


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
output_file="/iotlab/users/$user/.iot-lab/$experiment/sniffer/$host.oml"
echo "Content of the sniffer output on the gatweay container ($output_file)"
docker exec gateway_test cat $output_file

