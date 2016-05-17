Install
=======

Installing
----------

The install procedure is made for systems compatible with `update-rc.d`

Installing the application is done by running

    sudo python setup.py release

And server can be started with

    /etc/init.d/gateway-server-daemon restart

Or by restarting the host


It is a good idea to check the `post_install` part from `setup.py` script.
And if your system does not comply go to the next part.


### Other systems ###

Only install the python application with

    sudo python setup.py install

Then adapt `post_install` steps from `setup.py` for your system and run it
yourself.

> That is what is done for `OpenEmbedded` packet building system.


Configuration
-------------

The configuration is stored in

    ls /var/local/config/
    board_type  control_node_type  hostname

* `board_type`: open node type `['M3', 'A8', ...]`
* `control_node_type`: open node type `['iotlab', 'no']` default `iotlab`
* `hostname`: hostname to use format should be `'{board_type}-{num}[-ANYTHING]'`

User measure files
------------------

User measure files and logs will be stored in `/iotlab/users`.

Result files are either created by `site-manager` when filesystem is mounted
over nfs, or should be created manually if it is not the case.

In the last scenario, `www-data` user should be allowed to write in this
directory.


Dependencies
------------

### openocd ###

With 'ft2232' support for m3/fox nodes
With 'cmsis-dap' and 'hidapi-libusb' for samr21-xpro node

Currently running version 0.9.0 with following compile options

    --enable-legacy-ft2232_libftdi --disable-ftdi2232 --disable-ftd2xx
    --enable-cmsis-dap --enable-hidapi-libusb


### avrdude ###

Tested version 6.0.1

Required for leonardo/mega arduino nodes


### socat ###

For serial redirection.


### iot-lab-ftdi-utils ###

[iot-lab-ftdi-utils](https://github.com/iot-lab/iot-lab-ftdi-utils/)

Compiled and installed in `/usr/bin` or `/usr/local/bin`.


### liboml2 ###

[oml](https://mytestbed.net/projects/oml)

Tested version 2.11 compiled from source.
