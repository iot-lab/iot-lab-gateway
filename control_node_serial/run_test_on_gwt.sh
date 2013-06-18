#! /bin/bash

TARGET=gateway-m3
set -x
QUIET='-q'

make || exit 42
make clean

git clean -fdX $QUIET
scp -r $QUIET ../control_node_serial/ ${TARGET}:
ssh -t ${TARGET} 'source /etc/profile; cd fit-dev/gateway_code_python/; ./flash_firmware gwt static/control_node.elf'
ssh -t ${TARGET} 'cd control_node_serial;  make clean all && { python -u ./examples/send_commands.py examples/test_commands | make run; }'

