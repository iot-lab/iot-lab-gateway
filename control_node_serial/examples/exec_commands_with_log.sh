#! /bin/bash
set -x

test_file=$1

stdout_file="output.log"
stderr_file="debug.log"

make -C ..
python -u send_commands.py  $test_file | ../control_node_serial_interface -d > >(tee $stdout_file) 2> >(tee $stderr_file >&2)
