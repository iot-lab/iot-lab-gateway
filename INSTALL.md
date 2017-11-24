Install
=======

Tested on Ubuntu 14.04 LTS.

To simplify this setup, we've developed a Docker image, see `DOCKER.md`


Dependencies
------------

### Mandatory ###

```
sudo apt-get install python-dev python-setuptools socat
```

#### liboml2 ####

[oml](https://mytestbed.net/projects/oml)

https://oml.mytestbed.net/projects/oml/wiki/BuildingSource

Tested version 2.11 compiled from source.

```
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
sudo make install
```
#### CC2538 ####

Required for nodes equiped with Zoul module (such as Firefly node)

```
git clone https://github.com/JelmerT/cc2538-bsl &&\
sudo cp cc2538-bsl/cc2538-bsl.py /usr/bin/.
sudo apt-get update &&\
sudo apt-get install -y binutils
pip install intelhex
pip install python-magic #optional
```

Installing
----------

The install procedure is made for systems compatible with `update-rc.d`

Installing the application is done by running

    sudo python setup.py install
    sudo python setup.py post_install

In order to take into account the www-data user into dialout group, restart a new session or reboot computer.

> Check `post_install` steps from `setup.py` for other GNU/Linux distrib.

Check home_dir for user www-data, if not exists :

```
sudo mkdir /var/www
sudo chown www-data:www-data /var/www
```


Configuration
-------------

Create directory /var/local/config/ for configuration files  :

* `board_type`: open node type `['M3', 'A8', 'SAMR21', ...]`
* `control_node_type`: open node type `['iotlab', 'no']` default `iotlab`
* `hostname`: hostname to use format should be `'{node}-{num}[-ANYTHING]'`


Example below for SAMR21

```
sudo mkdir /var/local/config/
echo "SAMR21" | sudo tee /var/local/config/board_type
echo "no" | sudo tee /var/local/config/control_node_type
echo "custom-123" | sudo tee /var/local/config/hostname
```

And server can be started with

    sudo /etc/init.d/gateway-server-daemon restart

Or by restarting the host


Test installation
-----------------

User measure files and logs will be stored in `/iotlab/users`.

Result files are either created by `site-manager` when filesystem is mounted
over nfs, or should be created manually if it is not the case.

In the last scenario, `www-data` user should be allowed to write in this
directory.

In order to test a stand-alone iot-lab-gateway installation (e.g. for user test
and expid 123) please create the following directories and launch test scripts
:

```
sudo mkdir -p /iotlab/users/test
sudo chown www-data:www-data /iotlab/users/test
./tests_utils/curl_scripts/start_exp_fw_custom.sh gateway_code/static/samr21_autotest.elf
```

Interact with the auto_test firmware :

```
nc localhost 20000
help
Command              Description
---------------------------------------
echo                 Simply write 'echo'
get_time             Simply return current timer value
leds_on              Turn led on
leds_off             Turn led off
```

Stop experiment :

```
./tests_utils/curl_scripts/stop_exp.sh
```
