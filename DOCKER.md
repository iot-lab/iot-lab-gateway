Docker Image of iot-lab-gateway
===============================

The included Dockerfile includes all the necessary dependencies listed in [INSTALL.md](INSTALL.md), without you having
to install them on your host machine.

The only prerequisite before running the image for the first time is installing udev rules on the host. The udev rules create a subdirectory /dev/iotlab

    python setup.py udev_rules_install

For the following commands sudo might be needed depending on whether your user is in the `docker` group:

To build the image :

    make build-docker-image

To run the image:

    make BOARD={node_name} run

To specify a certain hostname, use the HOSTNAME variable

    make HOSTNAME=custom-m3-00 BOARD=m3 run

To bind the server on a certain host or port:

    make PORT=8081 HOST=0.0.0.0 HOSTNAME=custom-m3-00 BOARD=m3 run

By default the current working directory is bound inside the container
and this is this code that is run. Be advised, the disadvantage is that
some files might be created in the current working directory with `root`
permissions (the user inside the Docker container)
