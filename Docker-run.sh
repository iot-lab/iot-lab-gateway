docker run \
  -v /home/cedric/POLYTECH/stage/Environnement/Work/iot-lab-gateway/:/setup_dir/iot-lab-gateway/ \
  --rm \
  -p 8080:8080 \
  -p 20000:20000 \
  --name "gateway_test" \
  --privileged \
  -v /dev:/dev \
  iot_gateway
