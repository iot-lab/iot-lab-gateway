#! /bin/bash

set -x

make || exit 42

git clean -fdX -q
scp -r -q ../control_node_interface/ gw-m3:
ssh -t gw-m3 'cd fit-dev/gateway_code_python/; ./control_node_interaction consumption start 3.3V --average 1 --period 140us -p -v -c'
ssh -t gw-m3 'cd control_node_interface; make run'

