IoT-LAB Gateway
===============


[![Build Status](https://github.com/iot-lab/cli-tools/workflows/CI/badge.svg)](https://github.com/iot-lab/cli-tools/actions?query=workflow%3ACI+branch%3Amaster)
[![codecov](https://codecov.io/gh/iot-lab/iot-lab-gateway/branch/master/graph/badge.svg)](https://codecov.io/gh/iot-lab/iot-lab-gateway)


This is the Python code that runs on the gateway for the FIT IoT-LAB
platform. It serves an API for starting, stopping experiments, flashing firmwares.

For a description of the hardware on which this code is usually run, see a [General overview](https://www.iot-lab.info/hardware/#iot-lab-node)
and [Gateway Hardware](https://github.com/iot-lab/iot-lab/wiki/Hardware_Iotlab-gateway). It can also be run on
many hardware, including Raspberry Pi. 


* If you want to run this code on your own, we recommend you use the Docker-based procedure [DOCKER.md](DOCKER.md)


* If you want to manually install all the dependencies, you should read [INSTALL.md](INSTALL.md)


Once the gateway API is running, it will be accessible on `localhost:8080` 
and can be queried using curl, look at the directory `tests_utils/curl_scripts` for documented examples

* If you want to add support for a new custom open node, you should read [DEVELOPER.md](DEVELOPER.md)


This code is integrated into a Yocto image (see https://github.com/iot-lab/iot-lab-yocto)
on which each gateway boots remotely. The configuration of the API (specifying what board is connected, etc)
is done through a directory /var/local/config that is a NFS mount. Monitoring data (logs, radio & consumption monitoring)
is written inside the /iotlab folder which is also a NFS mount
