#! /bin/bash

set -x

make || exit 42

git clean -fdX -q
scp -r -q ../control_node_interface/ gw-m3:
ssh gw-m3 'cd control_node_interface; make run'

