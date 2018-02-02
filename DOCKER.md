Docker Image of iot-lab-gateway
===============================

The included Dockerfile includes all the necessary dependencies listed in `INSTALL.md`, without you having
to install them on your host machine.

For the following commands sudo might be needed depending on whether your user is in the `docker` group:

To build the image :

    docker build -t iot-lab-gateway .

To run the image, assuming the open node is plugged and assigned to /dev/ttyUSB0:

    ./docker-run /dev/ttyUSB0

Command line arguments for docker-run:

    usage: docker-run [--help] [-v VOLUME] [-b BOARD_TYPE] [-h HOSTNAME]
                      [-c CONTROL_NODE_TYPE] [-d] [-r] [--cntty CNTTY]
                      ontty

    positional arguments:
      ontty                 Open Node tty to pass inside the docker container

    optional arguments:
      --help
      -v VOLUME, --volume VOLUME
                            Host directory containing gateway_code (default: )
      -b BOARD_TYPE, --board-type BOARD_TYPE
                            Set node board type (default: m3)
      -h HOSTNAME, --hostname HOSTNAME
                            Set hostname (default: custom-123)
      -c CONTROL_NODE_TYPE, --control-node-type CONTROL_NODE_TYPE
                            Set node as control node (default: no)
      -d, --daemon          Daemon mode (default: False)
      -r, --reloader        Reloader (default: False)
      --cntty CNTTY         Control Node tty to pass inside the docker container


You can mount a gateway_code folder into the docker container, so that you can modify your code, and have it used inside the container
directly, usually:

    ./docker-run -v gateway_code /dev/ttyUSB0

## Examples

You can use any type of open node:

    ./docker-run -b samr21 -h samr21-test1 /dev/ttyACM0

You can mount your gateway_code and have the gateway API auto reload on code change, working in the background

    ./docker-run -v gateway_code --reloader /dev/ttyUSB0

You can have the gateway run in the background by using a `-d` or `--daemon` argument

    ./docker-run -d /dev/ttyUSB0

Once the gateway runs in the background with `docker-run -d`, you can interact with its REST server on `http://localhost:8080`, and the serial port
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

Build the docker image and run `docker-run` as explained above.
