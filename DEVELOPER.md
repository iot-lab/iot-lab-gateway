Introduction
============

[TODO]
The IoT-LAB experimental platform allows users to conduct remote
experiments on wireless sensor board (such as an Arduino board with an
Xbee module). For this purpose,a board called *open-node*, can be
connected to the IoT-LAB gateway, via the usb port. Below, the picture
of an open-node connected to a gateway.

![Gateway and wireless sensor board (e.g. Fox node)](gateway.jpg)

On the linux distribution installed on the gateway, runs a Python module providing a REST API for open-node management. The gateway can perform open-node commands like flashing a firmware or switch on his power supply. This document shows how to integrate a new open-node in the Iot-Lab platform. This integration is based on a plugin system provided by the Python module.
[/TODO]

Requirements
============

Your node must be powered by USB. You must have developed at least
two firmwares for your node: an autotest firmware and an idle firmware
(described below).

Adding a new open-node
======================

You can get the Python module code by cloning the git repository:

    $ git clone git@github.com:iot-lab/iot-lab-gateway.git

You will need to implement:

* firmwares
* node_ Python class
* udev rules


Module architecture
-------------------

This section present the module architecture.

        |
        +-gateway_code/
        |   |
        |   +-static/..... Contains the firmwares and the configuration file
        |   |   |
        |   |   +-----m3_idle.elf
        |   |   +-----m3_autotest.elf
        |   |   +-----[...]
        |   |
        |   +-open_nodes/... Contains the code to interact with the open-node, you will put your code here
        |       |
        |       +-----node_m3.py
        |       +-----[...]
        |
        +-bin/
            |
            +-rules.d .................. Directory for the udev rules
                +-----m3.rules
                +-----[...]


Between two plugs, the device name as detected by the
embedded linux running on the gateway can change: for example,
an unique device can be successively detected as ttyUSB0 and then
as ttyUSB1. As it is essential to have a fixed name for your device,
you have to write a udev rules specific for your device. To do such a
thing, you must create a file named `your_node.rules` (with `your_node`
the name of your node). Using the command `udevadm`, you have to
retrieve some information to identify your node such as the serial
id, the vendor id or the product id. You must set a name for the
device and set the right group (dialout) and the right mode (664).
The convention is to name device `ttyON_NODENAME`.
Below the example of the udev rule for the M3 node:

    SUBSYSTEM=="tty", SUBSYSTEMS=="usb", ENV{ID_SERIAL}=="IoT-LAB_M3",
    ENV{ID_USB_INTERFACE_NUM}=="01",  SYMLINK+="ttyON_M3"

    SUBSYSTEM=="usb", ATTR{idProduct}=="6011", ATTR{idVendor}=="0403",
    MODE="0664", GROUP="dialout"

Plugin integration
------------------

### Naming convention

As said previously, the application is based on a system of plugin: if
you want to add a node, you just have to write a specific file to
interface with the application. When the application is launched,
it reads the name of your open node located in the file

    /var/local/config/board_type

and then will use the class named Node{nameofyournode} located in

    gateway_code/open_node/node_{nameofyournode}.py

to manage the experiment.

If the name of your class or if your file is not formatted the right way, an
explicit error will be raised at launch.

### Interface of the node class

The gateway code expects certain attributes and methods from
the class for your custom open node.

During the experiment and the tests, the application use several
attributes located in your class. These attributes are the characteristics
of your node and we can find for example, the name of your device as
chosen in the udev rules (e.g. TTY); the baudrate which allows the
communication between the gateway and your node (e.g. BAUDRATE).

The API provides services. These services are loaded dynamically,
concerning what your open-node allows to do. These services are based on
method implemented in your file: if the API need a specific method to
create a service, the gateway_code will check if your class implements
this method. If it doesn’t, the service will not be available.

Some services are always needed, such as the start and stop of an experiment.
The methods required by these services are mandatory and are the following:

+ `setup`: Perform all the actions required to properly start an experiment.
+ `teardown`: Perform all the actions required to properly stop an experiment.
+ `flash`: Flash a firmware on the open-node.

Other services will be available if the corresponding methods are implemented.
These methods are the following:

+ `reset`: Reset the open-node.
+ `debug_start`: Start the open-node debugger.
+ `debug_stop`: Stop the open-node debugger.

Do not hesitate to watch the other implementations of open nodes to have
a better idea of what the application expects. For an example, you can
look at `doc/node_example.py`

### Errors and return values

When one of the function described above terminates with a success, the
return value must be 0. When the return value is different from 0, the
application know that something gone wrong. Except status, all the method
in the template file return an error.

### Flashing the open node

Some methods such as `reset`, `flash` or `debug_start`, need to interact
with the serial port of the open node. To do this, you will have to use
a programmer software and write code to interact with it. `Openocd`,
`Avrdude`, and others, are already available but maybe you will need to use another
programmer and implement your own python file in the `gateway_code/utils/`
folder.

Writing firmwares
-----------------

To add your custom node in the IoT-Lab platform, you must write two
firmwares. These firmwares must be put
in the `gateway_code/static/` folder

### Idle firmware

The idle firmware, must be a program with a consumption as low as
possible (no led blinking, and no infinite loop). This firmware is
flashed on the open node when no experiment is running.

### Autotest firmware

The autotest firmware is used during the testing phase. IotLAB-platform
allows you to perform autotests for your device. It could be useful to
see if the sensor on your node are still alive and send valid
data. During the testing phase, the gateway will flash the autotest
firmware on the open-node and will then send some commands to the
open-node. For example, if your node embeds a light sensor, the gateway
will send the following command on the serial port: `get_light`. Your
autotest firmware will receive this order, ask to the light sensor a
measure and then send back to the gateway: `ACK get_light <value_of_measure> lux`. Thanks to this, the gateway will
know that the light sensor on your open-node works. An annex
file gather all the autotest command which can be send by the gateway.
Among all these tests, one is mandatory: `echo`.

This test ensures that your open-node is answering on the serial.
`echo` command must behave as described bellow:

    Gateway message : 'echo HELLO WORLD'
    Node answer : 'HELLO WORLD'

    Gateway message : 'echo ACK'
    Node answer : 'ACK'

To inform the application what kind of command your autotest firmware
can handle, you must write the name of the test in the list
`AUTOTEST_AVAILABLE` as shown in the template file.

You can find the code (based on RIOT operating system) for the autotest and idle
firmwares for some boards supported on IoT-LAB
on [ci-firmwares](https://github.com/iot-lab/ci-firmwares)

Testing your implementation
===========================

We've provided Dockerfiles with all the dependencies and a Makefile
for you to build and use them. (if using MacOS, see Appendix below)

Using Docker
------------

If you want to run tests with the Docker images, first build them:

    make build-docker-image-test

### Unit tests

The purpose of unit tests is to verify your Python code,
independently from connections to a physical board.

To run the unit tests with the provided Docker image, just run:

    make test

### Integration tests

The purpose of integration tests is to verify that your flashing tool
and firmwares behave as expected when called by the gateway code.

To run the integration tests with the provided Docker image, just run:

    make BOARD={node_name} integration-test

without Docker
--------------

You will need to manually install all the needed
dependencies, see [INSTALL.md](INSTALL.md), and `tox`
for running the tests.

> If you don't have tox, install it with
>
>     pip install tox

### Unit tests

Run:

    make local-test

### Integration tests

Run:

    make BOARD={node_name} local-integration-test

This will create a temporary config directorty,
containing the board_type and hostname,
equivalent to the /var/local/config in the IoT-LAB infrastructure,
and run `tox -e test`

Appendices
==========

Autotests available
-------------------

Bellow you will find commands that can be sent by the gateway during the
tests and the corresponding format of the return expected.


| Command                             | Expected answer format                 |
| ----------------------------------- | -------------------------------------- |
| `echo arg1 arg2 ...`                | `arg1 arg2 ...`                        |
| `get_time`                          | `ACK get_time 122953 T_UNIT`           |
| `get_uid`                           | `ACK get_uid 05D8FF323632483343037109` |
| `get_gyro`                          | `ACK get_gyro X. Y. Z. dps`            |
| `get_magneto`                       | `ACK get_magneto X. Y. Z. gauss`       |
| `get_accelero`                      | `ACK get_accelero X. Y. Z. g`          |
| `get_pressure`                      | `ACK get_pressure P. mbar`             |
| `get_light`                         | `ACK get_light L. lux`                 |
| `test_gpio`                         | `ACK test_gpio`                        |
| `test_i2c`                          | `ACK test_i2c`                         |
| `radio_pkt [channel] [power]`       | `ACK radio_pkt CHANNEL POWER`          |
| `radio_ping_pong [channel] [power]` | `ACK radio_ping_pong CHANNEL POWER`    |
| `leds_on [flag]`                    | `ACK leds_on [flag]`                   |
| `leds_off [flag]`                   | `ACK leds_off [flag]`                  |
| `leds_blink [flag] [time]`          | `ACK leds_blink [flag] [time]`         |
| `test_pps_start`                    | `ACK test_pps_start`                   |
| `test_pps_get`                      | `ACK test_pps_get`                     |
| `test_pps_stop`                     | `ACK test_pps_stop`                    |


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
