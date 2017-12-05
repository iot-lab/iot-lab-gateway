IoT-Lab Gateway
===============

This is the Python code that runs on the gateway for the FIT IoT-lab
platform. It serves an API for starting, stopping experiments, flashing firmwares.

For a description of the hardware, see a [General overview](https://www.iot-lab.info/hardware/#iot-lab-node) and [Gateway Hardware](https://github.com/iot-lab/iot-lab/wiki/Hardware_Iotlab-gateway)

If you want to run this code on your own, you have two choices:

* (Recommended) Using the provided Docker image

    make BOARD={node_name} run

    (e.g. BOARD=arduino_zero)

* Installing manualy all the dependencies, you should read [INSTALL.md](INSTALL.md)


If you want to create support for a new custom open node, you should read [DEVELOPER.md](DEVELOPER.md)


This code is integrated into a Yocto image (see https://github.com/iot-lab/iot-lab-yocto)
on which each gateway boots