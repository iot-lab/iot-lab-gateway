docker run \
  -v /home/cedric/POLYTECH/stage/Environnement/Work/iot-lab-gateway/:/setup_dir/iot-lab-gateway/ \
  -d \
  -p 8080:8080 \
  --name "gateway_test" \
  iot_gateway


#docker run \
#  -e "NODE_ENV=production" \ #env var declaration
#  -u "app" \ #username
#  -p 8080:8080 \
#  -w "/usr/src/app" \ #workdir
#  --name "gateway_test" \
#  -d \ #dettached mode
#  -ti \ #open tty, with interactive mode
#  iot_gateway
