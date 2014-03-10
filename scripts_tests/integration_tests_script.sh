#! /bin/bash

if [[ ( $# != 1 ) && ( $# != 2 ) ]]
then
    echo "Usage: $0 <hostname> [ssh_config_file]" >&2
    exit 1
fi


if [[ $# == 2 ]]
then
    SSH_CONFIG="$(readlink -e $2)"
else
    SSH_CONFIG="$(readlink -e ~/.ssh/config)"
fi
HOSTNAME="$1"

SRC_DIR="$(readlink -e $(dirname $0)/..)"
DEST="/tmp/fit-dev/"


set -x

# update gateway_code_python to host with www-data:www-data as owner
rsync -e "ssh -F $SSH_CONFIG" -av --delete   $SRC_DIR   $HOSTNAME:$DEST
ssh -F $SSH_CONFIG   $HOSTNAME "chown -R www-data:www-data $DEST"

#############
# Run tests #
#############

# run python tests
ssh -F $SSH_CONFIG   $HOSTNAME "su www-data -c '\
    source /etc/profile; \
    python $DEST/gateway_code_python/setup.py integration'"
    #python $DEST/gateway_code_python/setup.py integration --stop'"

# run control_node_serial tests
ssh -F $SSH_CONFIG   $HOSTNAME "\
    source /etc/profile; \
    make -C $DEST/gateway_code_python/control_node_serial realclean coverage"

# Get results files
rsync -e "ssh -F $SSH_CONFIG" -av \
    --include='*/' --include='*xml' --include='*out' --exclude='*'  -av \
    $HOSTNAME:$DEST $SRC_DIR/.. | grep -v "sender"
