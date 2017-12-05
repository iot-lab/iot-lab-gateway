Install
=======

This installs the dependencies for running the iot-lab-gateway code

Tested on Ubuntu 14.04 LTS.

Dependencies
------------

### Mandatory ###

```
sudo apt-get install python-dev python-setuptools socat
```

#### liboml2 ####

Tested version 2.11 compiled from source.

```
git clone https://github.com/mytestbed/oml.git && \
cd oml && \
git checkout tags/v2.11.0 && \
./autogen.sh && \
./configure --disable-doc --disable-doxygen-doc --disable-doxygen-dot \
    --disable-android --disable-doxygen-html --disable-option-checking && \
make && \
sudo make install && \
cd .. && rm -rf oml
```

### Optional  ###

If you want to be able to flash boards, you will need flashing tools,
depending on which board you want to test or support:


| Flashing tool  | Corresponding boards           |
| -------------- |:------------------------------:|
| openocd 0.9    | m3, samr21, fox                |
| openocd 0.10.0 | st_lrwan1                      |
| avrdude        | arduino_zero, leonardo         |
| cc2538-bsl     | firefly                        |
| pyOCD          | microbit                       |
| edbg(flash)    | samr21, arduino_zero           |

#### openocd 0.9.0 ####

Required for M3/samr21 and other nodes

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

#### openocd 0.10.0 ####

```
git clone https://github.com/ntfreak/openocd openocd10 && \
    cd openocd10 && \
    git checkout v0.10.0 && \
    ./bootstrap && \
    ./configure --prefix=/opt/openocd-0.10.0 --enable-cmsis-dap --enable-hidapi-libusb && \
    make && \
    sudo make install && \
    cd .. && rm -rf openocd10
```

#### avrdude ####

Required for leonardo/mega/zigduino arduino nodes

Tested version 6.0.1

```
sudo apt-get install avrdude
```

#### cc2538-bsl ####

Required for nodes equiped with Zoul module (such as Firefly node)

```
git clone https://github.com/JelmerT/cc2538-bsl && \
cp cc2538-bsl/cc2538-bsl.py /usr/bin/. && \
apt-get update && \
apt-get install -y python-pip binutils && \
pip install intelhex
```

#### pyOCD ####

```
pip install pyOCD
```


Local installation of the gateway_code
--------------------------------------

The install procedure is made for systems compatible with `update-rc.d`

Installing the application is done by running

    sudo python setup.py release

In order to take into account the www-data user into dialout group, restart a new session or reboot computer.

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
