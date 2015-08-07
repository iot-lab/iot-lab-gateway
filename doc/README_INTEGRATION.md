Introduction
============

The Iot-LAB experimental platform allow users to conduct remote
experiments on wireless sensor board (such as an arduino board with an
Xbee module). For this purpose,a board called *open-node*, can be
connected to the IoT-LAB gateway, via the usb port.Bellow, the picture
of an open-node connected to a gateway.

![Gateway and wireless sensor board (e.g. Fox node)](gateway.jpg "fig:")
[Gateway and wireless sensor board (e.g. Fox node)]

On the linux distribution installed on the gateway, a Python module
running provides a REST API able to receive remote commands to manage
the open-node. The gateway can perform open-node commands like flashing
a firmware in the open-node or starting his power supply on. This
document show how to integrate a new open-node in the Iot-Lab
platform.This integration is based on a plugin system provides by the
Python module.

Requirement
===========

Your node must be powered by USB.You must have developed at least two
firmwares for your node : an autotest firmware and an idle firmware
(describe in section bellow).

Adding a new open-node
======================

You can get the Python module code by cloning the git repository :

    $git clone git@github.com:iot-lab/iot-lab-gateway.git

Module architecture
-------------------

This section present the module architecture.
|
+-bin/
| |
| +-----rules.d .................. Directory for the udev rules
| +-----m3.rules
| +-----a8.rules
|
+-gateway_code/
| |
| +-----rest-server.py ........... The API entry point
| +-----common.py
| +-----gateway_manager.py
| +-----autotest/...............................Directory for all the autotests
| +-----utils/.. Contains script for serial operation such as serial redirection or programmer
|        |
|    +-----avrdude.py
|    +-----openocd.py
|
+-------static/..... Contains the firmwares and the configuration file
|    |
|        +-----idle_m3.elf
|    +-----m3_autotest.elf
|    +-----iot-lab-m3.cnf
+-------open_nodes/... Contains the code to interact with the open-node, you will put your code here
     |
     +-----node_a8.py
     +-----node_m3.py
     +-----node_fox.py
     +-----node_leonardo.py
     +-----node_mega.py


Udev rules
----------

Between two plugs, the name of the device as detected by the embedded
linux running on the gateway can change : for example, an unique device
can be succesively detected as ttyUSB0 and then as ttyUSB1.As it is
essential to have a fixed name for your device, you have to write a udev
rules specific for your device.To do such a thing, you must create a
file named your\_node.rules (with your\_node the name of your
node).Using the command udevadm, you have to retrieve some information
to identify your node such as the serial id, the id vendor or the id
product. You must set a name for the device and set the right group
(dialout) and the right mode (664). The convention is to name device
ttyON\_NODENAME. Bellow the example of the udev rule for the node M3 :

    SUBSYSTEM=="tty", SUBSYSTEMS=="usb", ENV{ID_SERIAL}=="IoT-LAB_M3", 
    ENV{ID_USB_INTERFACE_NUM}=="01",  SYMLINK+="ttyON_M3"

    SUBSYSTEM=="usb", ATTR{idProduct}=="6011", ATTR{idVendor}=="0403", 
    MODE="0664", GROUP="dialout"

Plugin integration
------------------

### Naming convention

As said previously, the application is based on a system of plugin : if
you want to add a node, you just have to write a specific file to
interface with the application.When the application is launched, the
gateway take the name of your node located in the file

    /var/local/config/board_type

and then will use the class named Node{nameofyournode} located in

    gateway-code/open_node/node_{nameofyournode}.py

to manage the expreriment. For example, if the name smt32nucleo is
register on the gateway, the class used by the gateway will be

    NodeStm32nucleo 

in the file

    gateway-code/open_node/node_stm32nucleo.py

If the name of your class or of your file not right formatted, an
explicit error will be raised at the launch of the application.

### Interfacing the python code

During the experiment and the tests, the application use several
attributes located in your class. This attributes are the characteristic
of your node and we can find for example, the name of your device as
chosen in the udev rules (e.g. TTY); the baudrate which allow the
communication between the gateway and your node (e.g. BAUDRATE).The list
of the mandatory attributes are present in the template file in the
annex. These attribute are required by the gateway for a good
working.You can add your own attribute if needed by your class.

The API provide services. These services are loaded dynamically,
regarding what your open-node allow to do. These services are based on
method implemented in your file : if the API need a specific method to
create a service, the gateway-code will check if your class implement
this method. If it doesn’t, the service will not be available.

Some service are always available such as the start and stop of an
experiment. The method required by these service are mandatory and are
the folowing :

setup
:   \
    Perform all the action required to properly start an experiment.

teardown
:   \
    Perform all the action required to properly stop an experiment.

flash
:   \
    Flash a firmware on the open-node.

Others methods are not mandatory and can be implemented if you need
them. The corresponding service will be available. These functions are
the following :

-   debug\_start

-   debug\_stop

-   reset

A template file given in annex gather all the functions which interface
with the code of the gateway.Here is a simple illustration of the
execution of the start of the start\_exp command.

![Command execution diagram](diag.jpg "fig:") [Command execution diagram]

Do not hesitate to watch the others implementation of open node to have
a better idea of what the application expect.

### Errors and return values

When one of the function describe above terminate with a success, the
return value must be 0.When the return value is different from 0, the
application know that something gone wrong.Except status, all the method
in the template file return an error.

### Flashing the open node

Some method such as “reset”, “flash” or “debug\_start”, need to interact
with the serial port of the open node. To do this, you will have to use
a programmer software and write code to interact with it. Openocd and
Avrdude are already available but maybe you will need to use another
programmer and implement your own python file in the folder
/gateway\_code/utils/.

Writing firmwares
-----------------

To add your code in the IoT-Lab platform, you must have writen two
firmware. These firmware must be put in the folder
/gateway\_code/static/ as shown by the directory architecture.

### Idle firmware

The idle firmware, must be a program with a consumption as low as
possible (no led blinking, and no infinite loop). This firmware is
flashed on the open node when no experiment are running.

### Autotest firmware

The autotest firmware is used during the testing phase. IotLAB-platform
allow you to perform autotests for your device. It could be useful to
see if the sensor on your node are still alive and send valid
datas.During the testing phase, the gateway will flash the autotest
firmware on the open-node and will then send some commands to the
open-node. The gateway will expect the open-node to answer these
command. For example, if your node embeds a light sensor, the gateway
will send the following command on the serial port : `get_light`. Your
autotest firmware will receive this order, ask to the light sensor a
measure and then send back to the gateway :
`ACK get_light value_of_measure lux`. Thanks to this, the gateway will
know that the light sensor on your open-node is still working.A annex
file gather all the autotest command which can be send by the gateway.
In all these test, one is mandatory : the test\_echo. This test ensure
that your open-node is still responding.The `echo` command must behave
as describe bellow :

    Gateway message : 'echo HELLO WORLD'
    Node answer : 'HELLO WORLD'

    Gateway message : 'echo ACK'
    Node answer : 'ACK'

To inform the application what kind of command your autotest firmware
can handle, you must write the name of the test in the list
AUTOTEST\_AVAILABLE as shown in the template file.When developing your
implementation, it’s possible to launch all the tests (and also the
autotest) using the following command :

    fab -f tests_utils/integration_fabfile.py python_test -H adress-of-your-node

Annex
=====

template file
-------------

Bellow you can find a template file which interface with the gateway
application with proper comment, free to you to use it and modify it :

    # -*- coding:utf-8 -*-
    """ Blank file for the implemention of an open-node called Nodename """

    from gateway_code.config import static_path
    from gateway_code import common
    from gateway_code.common import logger_call

    import logging
    LOGGER = logging.getLogger('gateway_code')


    class NodeNodename(object):

        TTY = '/dev/ttyON_NODENAME'
        # The tty as named in the udev rule
        BAUDRATE = 9600
        # The baudrate used to communicate with the open-node on the serial port
        FW_IDLE = static_path('idle_nodename.elf')
        # The name of the idle firmware
        FW_AUTOTEST = static_path('nodename_autotest.elf')
        # The name of the autotest firmware
        ALIM = '5V'
        # The tension of alimentation (will be 5V in most of the case)

        AUTOTEST_AVAILABLE = ['test_echo']
                            ]
        # The list of autotest available for your node.
        # As describe in the document, 
        # this list must contain at least 'test_echo'

        def __init__(self):
            # The initialization of your class

        @logger_call("Node Nodename : Setup of Nodename")
        def setup(self, firmware_path):
            # Here you will perform all the necessary action needed
            # by your node before the start of an experiment.
            return 1

        @logger_call("Node Nodename : teardown of nodename node")
        def teardown(self):
            # Here you will perform all the necessary action to
            # properly terminate your node
            return 1

        @logger_call("Node Nodename : flash of nodename node")
        def flash(self, firmware_path=None):
            # Here 
            return 1

        @logger_call("Node Nodename : reset of nodename node")
        def reset(self):
            # Not implemented
            return 1

        def debug_start(self):
            # Here you will start the debug of your node
            return 1

        def debug_stop(self):
            # Here you will stop the debug of your node
            return 1

        @staticmethod
        def status():
            # Here you will check your node (for exemple with ftdi chip)
            # if you are unable to check your node, just return 0
            return 0
            

Autotests available
-------------------

Bellow you will find command that can be sent by the gateway during the
tests and the corresponding format of the return expected.

test\_echo
:   \
    Format of the answer : already describe in the autotest section.

test\_get\_time
:   \
    Format of the answer : ACK check\_get\_time 122953 tick\_32khz

test\_uid
:   \
    Format of the answer : ACK get\_uid 05D8FF323632483343037109.

test\_gyro
:   \
    Format of the answer : ACK get\_gyro 1.07625 1.75 5.2500002E-2 dps.

test\_magneto
:   \
    Format of the answer : ACK get\_magneto 4.328358E-2 6.716418E-2
    -3.880597E-1 gauss.

test\_accelero
:   \
    Format of the answer : ACK get\_accelero 3.6E-2 -1.56E-1 1.0320001
    g.

test\_gpio
:   \
    Format of the answer : ACK test\_gpio.

test\_i2c
:   \
    Format of the answer : ACK test\_i2c.

test\_radio\_ping\_pong
:   \
    Format of the answer : ACK test\_radio\_ping\_pong.

test\_radio\_with\_rssi
:   \
    Format of the answer : ACK test\_radio\_with\_rssi.

test\_consumption\_dc
:   \
    Format of the answer : ACK test\_consumption\_dc.

test\_leds\_with\_consumption
:   \
    Format of the answer : ACK test\_leds\_with\_consumption.

test\_pressure
:   \
    Format of the answer : ACK get\_pressure 9.944219E2 mbar.

test\_light
:   \
    Format of the answer : ACK get\_light 5.2001953E1 lux.

test\_flash
:   \
    Format of the answer : ACK test\_flash.

test\_gps
:   \
    Format of the answer : ACK test\_gps.

test\_consumption\_batt
:   \
    Format of the answer : ACK test\_consumption\_batt.