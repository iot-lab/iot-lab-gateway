#! /bin/bash

set -x

git clean -fdX
scp -r ../control_node_interface/ gw-m3:
ssh gw-m3 'cd control_node_interface; make run'

