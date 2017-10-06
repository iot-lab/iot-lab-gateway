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

Once the gateway runs in the background with `docker-run`, you can interact with its REST server on `http://localhost:8080`, and the serial port
of the node is redirected on `localhost` TCP socket on port `20000`.

## Running under macOS

Docker for Mac does not support adding a host device to a container (e.g. `docker run --device`). [source](https://docs.docker.com/docker-for-mac/faqs/#can-i-pass-through-a-usb-device-to-a-container)  
The use of [Docker Toolbox](https://docs.docker.com/toolbox/overview/) is recommended.

Start Docker Toolbox with the Docker Quickstart Terminal, then do this additionnal steps on the boot2docker VM used by Docker Toolbox:
1. Install udev rules.

        $ docker-machine ssh
        docker@default:~$ git clone https://www.github.com/iot-lab/iot-lab-gateway.git && cd iot-lab-gateway
        docker@default:~$ sudo cp bin/rules.d/* /etc/udev/rules.d/.
        docker@default:~$ sudo udevadm control --reload
1. Thanks to the VirtualBox GUI or via VBoxManage command line, add a USB device filter for the device to be used as Open Node.

        $ VBoxManage list usbhost
        $ VBoxManage usbfilter add 1 --target default --name M3 --vendorid 0403 --productid 6010
1. (optionnal) Thanks to the VirtualBox GUI or via VBoxManage command line, add a NAT port forwarding rule to be able to call `http://localhost:8080`from the host.

        $ VBoxManage controlvm default natpf1 "bottle,tcp,127.0.0.1,8080,,8080"
        $ VBoxManage controlvm default natpf1 "serial_redirection,tcp,127.0.0.1,20000,,20000"

Run `docker-build`and `docker-run` as explained above.
>>>>>>> 512ae0d... add documentation to run in a Docker container under macOS
