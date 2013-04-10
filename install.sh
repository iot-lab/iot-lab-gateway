#! /bin/bash -ex



python setup.py nosetests
python setup.py install


# install daemon script
cp  gateway-server-daemon  /etc/init.d
chmod  +x  /etc/init.d/gateway-server-daemon

# allow gateway-server to use serial ports
usermod  -G  dialout  www-data
