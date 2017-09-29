Docker Image of iot-lab-gateway
===============================

The included Dockerfile includes all the necessary dependencies listed in `INSTALL.md`:

* liboml2
* openocd 0.9.0
* iot-lab-ftdi-utils

To build the image:

    sudo .\docker-build

To run the image

  * Prerequisite, install udev rules
      python setup.py udev_rules_install
  * Then
      sudo .\docker-run

Command line arguments for docker-run:

    docker-run [--help] [-o OPT_DIR] [-b BOARD_TYPE] [-h HOST]
                [-c NODE_TYPE] [-d] [-r]
                [cmd]

    positional arguments:
    cmd                   Command to run inside the docker container

    optional arguments:
    --help
    -o OPT_DIR, --opt-dir OPT_DIR
                        Optional opt dir to mount gateway_code (default: None)
    -b BOARD_TYPE, --board-type BOARD_TYPE
                        Set node board type (default: m3)
    -h HOST, --host HOST  Set hostname (default: custom-123)
    -c NODE_TYPE, --node_type NODE_TYPE
                        Set control_node_type (default: no)
    -d, --daemon          Daemon mode (default: False)
    -r, --reloader        Reloader (default: False)

You can mount a gateway_code folder into the docker container so you can modify your code, and have it used inside the container
directly:

    .\docker-run -o gateway_code

You can use any type of open node:

    \docker-run -b samr21

You can have the gateway run in the background by using a `-d` or `--daemon` argument

<<<<<<< HEAD
Once the gateway runs in the background with `Docker-run`, you can interact with its REST server on `http://localhost:8080`, and the serial port
of the node is on `http://localhost:20000`
=======
Once the gateway runs in the background with `docker-run`, you can interact with its REST server on `http://localhost:8080`, and the serial port
of the node is redirected on `localhost` TCP socket on port `20000`.
>>>>>>> 26fdf0b... update `docker-run` usage
