#! /bin/bash
set -x

if [[ $# != 2 ]]; then
        echo "Usage: $0 <tty> <test_file>"
        exit 1
fi

tty=$1
test_file=$2

stdout_file="output.log"
stderr_file="debug.log"

python -u send_commands.py  $tty  $test_file  > >(tee $stdout_file) 2> >(tee $stderr_file >&2)
