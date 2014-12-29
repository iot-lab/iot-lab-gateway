#! /bin/bash
set -x

test_file=$1

make -C ..
python -u send_commands.py  $test_file | ../control_node_serial_interface -d
