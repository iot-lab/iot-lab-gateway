BOARD ?= m3

.PHONY: build-docker-image build-docker-image-test setup-udev-rules \
	    test integration-test

build-docker-image:
	docker build -t iot-lab-gateway .

build-docker-image-test: build-docker-image
	docker build -t iot-lab-gateway-tests tests

setup-udev-rules:
	sudo cp bin/rules.d/* /etc/udev/rules.d/.
	sudo udevadm control --reload-rules

test:
	docker run -t --rm \
		-v $(PWD):/shared \
		-e LOCAL_USER_ID=`id -u $(USER)` \
		iot-lab-gateway-tests tox

integration-test:
	cp -R $(PWD)/tests_utils/cfg_dir /tmp/.
	echo $(BOARD) > /tmp/cfg_dir/board_type
	echo $(BOARD)-00 > /tmp/cfg_dir/hostname
	docker run -t --rm \
		-v $(PWD):/shared \
		-v /dev/iotlab:/dev/iotlab \
		-v /tmp/cfg_dir:/shared/cfg_dir \
		-e LOCAL_USER_ID=`id -u $(USER)` \
		-e IOTLAB_GATEWAY_CFG_DIR=/shared/cfg_dir \
		--privileged \
		iot-lab-gateway-tests tox -e test
