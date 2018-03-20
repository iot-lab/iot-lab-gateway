BOARD ?= m3
HOST ?= 0.0.0.0
PORT ?= 8080
SERIAL_PORT ?= 20000
CONTROL_NODE_TYPE ?= no

.PHONY: build-docker-image build-docker-image-test setup-udev-rules \
	    test local-test \
	    integration-test local-integration-test \
	    run local-run \
	    setup-cfg-dir

build-docker-image:
	docker build -t iot-lab-gateway .

build-docker-image-test: build-docker-image
	docker build -t iot-lab-gateway-tests tests

setup-udev-rules:
	sudo cp bin/rules.d/* /etc/udev/rules.d/.
	sudo udevadm control --reload-rules

setup-cfg-dir:
	cp -R $(PWD)/tests_utils/cfg_dir /tmp/.
	echo $(BOARD) > /tmp/cfg_dir/board_type
	echo $(CONTROL_NODE_TYPE) > /tmp/cfg_dir/control_node_type
	echo $(BOARD)-00 > /tmp/cfg_dir/hostname

test:
	docker run -t --rm \
		-v $(PWD):/shared \
		-e LOCAL_USER_ID=`id -u $(USER)` \
		iot-lab-gateway-tests tox

integration-test: setup-cfg-dir
	docker run -t --rm \
		-v $(PWD):/shared \
		-v /dev/iotlab:/dev/iotlab \
		-v /tmp/cfg_dir:/shared/cfg_dir \
		-e LOCAL_USER_ID=`id -u $(USER)` \
		-e IOTLAB_GATEWAY_CFG_DIR=/shared/cfg_dir \
		--privileged \
		iot-lab-gateway-tests tox -e test

run: setup-cfg-dir
	docker run -it --rm \
		-v $(PWD):/shared \
		-v /dev/iotlab:/dev/iotlab \
		-v /tmp/cfg_dir:/var/local/config \
		-p $(PORT):8080 \
		-p $(SERIAL_PORT):20000 \
		--privileged \
		iot-lab-gateway

local-test:
	tox

local-integration-test: setup-cfg-dir
	IOTLAB_GATEWAY_CFG_DIR = /tmp/cfg_dir
	tox -e test

local-run: setup-cfg-dir
	IOTLAB_GATEWAY_CFG_DIR=/tmp/cfg_dir
	bin/scripts/gateway-rest-server $(HOST) $(PORT)
