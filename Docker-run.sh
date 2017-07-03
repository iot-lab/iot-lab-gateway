#!/bin/sh

Options=$@
OPT_DIR=""
BOARD_TYPE="M3"
CONTROL_NODE_TYPE="no"
HOSTNAME="custom-123"


_usage(){
  cat <<EOF
Docker-run.sh $Options
$*
Usage : Docker-run.sh <[options]>
Options :
  -b --board=...          Set node board type (default : $BOARD_TYPE)
  -h --host=...           Set hostname (default : $HOSTNAME)
  -c --node-type=...      Set control_node_type (default : $CONTROL_NODE_TYPE)
  --help                  Show this message
EOF
}


while getopts "c:b:h:d:-:" opt ; do
case $opt in
    b) BOARD_TYPE=$OPTARG; shift 2;;
    h) HOSTNAME=$OPTARG; shift 2 ;;
    c) CONTROL_NODE_TYPE=$OPTARG; shift 2 ;;
    d) DEVICE=$OPTARG; shift 2 ;;
    -) LONG_OPTARG="${OPTARG#*=}"
      case $OPTARG in
        board=?* ) BOARD_TYPE=$LONG_OPTARG; shift 1 ;;
        board* ) echo "No arg for --$OPTARG option" >&2; exit 2 ;;
        host=?* ) HOSTNAME=$LONG_OPTARG; shift 1 ;;
        host* ) echo "No arg for --$OPTARG option" >&2; exit 2 ;;
        node-type=?* ) CONTROL_NODE_TYPE=$LONG_OPTARG; shift 1 ;;
        node-type* ) echo "No arg for --$OPTARG option" >&2; exit 2 ;;
        help ) _usage ; exit 0 ;;
      esac
esac
done

if [ ! -z $1 ] ; then
  if [ -d $1 ] ; then
    echo "$1 mounted as gateway_code repository\n"
    OPT_DIR="-v $1:/usr/local/lib/python2.7/dist-packages/gateway_code-2.4.0-py2.7-linux-x86_64.egg/gateway_code"
  else
    echo "Please use a valid path.\n"
    exit 0
  fi
fi

cat<<EOF
Used config :
  BOARD_TYPE=$BOARD_TYPE, HOSTNAME=$HOSTNAME, CONTROL_NODE_TYPE=$CONTROL_NODE_TYPE
  Montage : $OPT_DIR
EOF

docker run \
  $OPT_DIR \
  --rm \
  -e BOARD_TYPE=$BOARD_TYPE \
  -e CONTROL_NODE_TYPE=$CONTROL_NODE_TYPE \
  -e HOSTNAME=$HOSTNAME \
  -p 8080:8080 \
  -p 20000:20000 \
  --name "gateway_test" \
  --privileged \
  -v /dev:/dev \
  -d \
  iot_gateway
