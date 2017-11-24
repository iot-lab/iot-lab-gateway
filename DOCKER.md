Docker Image of iot-lab-gateway
===============================

The included Dockerfile includes all the necessary dependencies listed in `INSTALL.md`, without you having
to install them on your host machine.

The only prerequisite before running the image for the first time is installing udev rules on the host

    python setup.py udev_rules_install

For the following commands sudo might be needed depending on whether your user is in the `docker` group:

To build the image :

    docker build -t iot-lab-gateway .

To run the image:

    ./docker-run

Command line arguments for docker-run:

    usage: docker-run [--help] [-v VOLUME] [-b BOARD_TYPE] [-h HOSTNAME]
                      [-c NODE_TYPE] [-d] [-r]
                      [cmd [cmd ...]]

    positional arguments:
      cmd                   Command to run inside the docker container (default:
                            None)

    optional arguments:
      --help
      -v VOLUME, --volume VOLUME
                            Host directory containing the gateway code, usually gateway_code (default: None)
      -b BOARD_TYPE, --board-type BOARD_TYPE
                            Set node board type (default: m3)
      -h HOSTNAME, --hostname HOSTNAME
                            Set hostname (default: custom-123)
      -c NODE_TYPE, --node_type NODE_TYPE
                            Set control_node_type (default: no)

    options:
      -d, --daemon          Daemon mode
      -r, --reloader        Reloader


You can mount a gateway_code folder into the docker container, so that you can modify your code, and have it used inside the container
directly, usually:

    ./docker-run -v gateway_code

## Examples

You can use any type of open node:

    ./docker-run -b samr21 -h samr21-test1

You can mount your gateway_code and have the gateway API auto reload on code change, working in the background

    ./docker-run -v gateway_code --reloader

You can have the gateway run in the background by using a `-d` or `--daemon` argument

    ./docker-run -d

Instead of launching the API, you can do something inside the container, like building the control node C interface:

    ./docker-run -- python setup.py build_ext



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
