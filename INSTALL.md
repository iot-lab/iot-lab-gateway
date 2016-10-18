Install
=======

Tested on Ubuntu 14.04 LTS.


Dependencies
------------

### Mandatory ###

```
sudo apt-get install  python-dev python-setuptools socat
```

#### liboml2 ####

[oml](https://mytestbed.net/projects/oml)

https://oml.mytestbed.net/projects/oml/wiki/BuildingSource

Tested version 2.11 compiled from source.

``
wget http://mytestbed.net/attachments/download/1104/oml2-2.11.0.tar.gz
tar xf oml2-2.11.0.tar.gz
cd oml2-2.11.0
./configure --disable-doc --disable-doxygen-doc --disable-doxygen-dot --disable-android --disable-doxygen-html --disable-option-checking
make
sudo make install
```

### Optional  ###

#### openocd ####

Required for M3/samr21 nodes

Currently running version 0.9.0 with following compile options

With 'ft2232' support for m3/fox nodes
With 'cmsis-dap' and 'hidapi-libusb' for samr21-xpro node

```
sudo apt-get install libhidapi-dev libusb-1.0-0-dev libftdi-dev autoconf build-essential
git clone https://github.com/ntfreak/openocd
cd openocd
git checkout v0.9.0
./bootstrap
./configure  --enable-legacy-ft2232_libftdi --disable-ftdi2232 --disable-ftd2xx --enable-cmsis-dap --enable-hidapi-libusb
make
sudo make install
```

#### avrdude ####

Required for leonardo/mega/zigduino arduino nodes

Tested version 6.0.1


```
sudo apt-get install avrdude
```

#### iot-lab-ftdi-utils ####

For M3 Nodes and Hikob IoT-LAB Gateway only.

[iot-lab-ftdi-utils](https://github.com/iot-lab/iot-lab-ftdi-utils/)

Compiled and installed in `/usr/bin` or `/usr/local/bin`.

```
make
make install
```

Installing
----------

The install procedure is made for systems compatible with `update-rc.d`

Installing the application is done by running

    sudo python setup.py install
    sudo python setup.py post_install

In order to take into account the www-data user into dialout group, restart a new session or reboot computer. 

> Check `post_install` steps from `setup.py` for other GNU/Linux distrib.
> Please check home_dir for user www-data, if not exists :

```
mkdir /var/www
chown www-data:www-data /var/www
```

Configuration
-------------

Create directory /var/local/config/ for configuration files  :

* `board_type`: open node type `['M3', 'A8', 'LEONARDO', ...]`
* `control_node_type`: open node type `['iotlab', 'no']` default `iotlab`
* `hostname`: hostname to use format should be `'{node}-{num}[-ANYTHING]'`


Example below for Arduino Leonardo

```
mkdir /var/local/config/
echo "LEONARDO" > /var/local/config/board_type
echo "no" > /var/local/config/control_node_type
echo "custom-123" > /var/local/config/hostname
```

And server can be started with

    /etc/init.d/gateway-server-daemon restart

Or by restarting the host

User measure files
------------------

User measure files and logs will be stored in `/iotlab/users`.

Result files are either created by `site-manager` when filesystem is mounted
over nfs, or should be created manually if it is not the case.

In the last scenario, `www-data` user should be allowed to write in this
directory.


