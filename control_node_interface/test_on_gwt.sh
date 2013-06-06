#! /bin/bash

TARGET=gateway-m3
set -x

make || exit 42
make clean

git clean -fdX -q
scp -r -q ../control_node_interface/ ${TARGET}:
ssh -t ${TARGET} 'cd fit-dev/gateway_code_python/; ./control_node_interaction consumption start 3.3V --average 1 --period 140us -p -v -c'
ssh -t ${TARGET} 'cd control_node_interface; make clean run'

