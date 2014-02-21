#! /bin/bash

if [[ ( $# != 1 ) && ( $# != 2 ) ]]
then
    echo "Usage: $0 <hostname> [ssh_config_file]" >&2
    exit 1
fi


HOSTNAME="$1"
SSH_CONFIG="$(readlink -e ~/.ssh/config)"

if [[ $# == 2 ]]
then
    SSH_CONFIG="$(readlink -e $2)"
fi



SCRIPT_DIR="$(dirname $0)"
SRC_DIR="$(readlink -e $SCRIPT_DIR/..)"

DEST="/tmp/fit-dev/"

set -x



# update gateway_code_python to host with www-data:www-data as owner
rsync -e "ssh -F $SSH_CONFIG" -av --delete   $SRC_DIR   $HOSTNAME:$DEST
ssh -F $SSH_CONFIG   $HOSTNAME "chown -R www-data:www-data $DEST"


#
# Run tests
#

# run integration tests
ssh -F $SSH_CONFIG   $HOSTNAME "\
    su www-data -c 'python $DEST/gateway_code_python/setup.py tests'"
    #su www-data -c 'python $DEST/gateway_code_python/setup.py integration'"

# run control_node_serial tests
ssh -F $SSH_CONFIG   $HOSTNAME "\
    source /etc/profile; \
    make -C $DEST/gateway_code_python/control_node_serial realclean test \
    coverage"





