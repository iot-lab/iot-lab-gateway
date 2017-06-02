FROM ubuntu:14.04
MAINTAINER Cédric Roussel <cedric.roussel@inria.fr>

#MANDATORY
RUN apt-get update &&\
    apt-get install -y git \
      python-dev \
      python-setuptools \
      socat &&\
    apt-get clean

#openocd
RUN apt-get update &&\
    apt-get install -y \
      build-essential \
      libftdi-dev \
      libhidapi-dev \
      libusb-1.0-0-dev \
      autoconf \
#./configure requires thoses packages :
      libsqlite3-dev \
      libpopt-dev \
      libxml2-dev \
#error /bin/bash : ruby: command not found
      ruby \
#./bootstrap requires libtool
      libtool \
#configure.ac error : this package seems to solve the problem
      pkg-config &&\
    apt-get clean

#AVR (arduino like)
RUN apt-get update &&\
    apt-get install -y \
      avrdude &&\
    apt-get clean


#Clean the apt cache to save image size

RUN mkdir /setup_dir
WORKDIR /setup_dir

#liboml2 install

RUN mkdir /var/www && chown www-data:www-data /var/www



#ADD pourrait extraire directement le fichier dans l'image (pas d'import nécessaire)
#ADD oml2-2.11.0.tar.gz /

COPY ./oml2-2.11.0.tar.gz /setup_dir
RUN tar xf oml2-2.11.0.tar.gz &&\
    cd ./oml2-2.11.0 &&\
    ./configure --disable-doc --disable-doxygen-doc --disable-doxygen-dot --disable-android --disable-doxygen-html --disable-option-checking &&\
    make &&\
    sudo make install &&\
    cd .. &&\
    rm -rf oml2-2.11.0 &&\
    rm oml2-2.11.0.tar.gz

#openocd install (for M3 and SAMR21)

RUN git clone https://github.com/ntfreak/openocd &&\
    cd openocd &&\
    git checkout v0.9.0 &&\
    ./bootstrap &&\
    ./configure  --enable-legacy-ft2232_libftdi --disable-ftdi2232 --disable-ftd2xx --enable-cmsis-dap --enable-hidapi-libusb &&\
    make &&\
    sudo make install &&\
    cd .. && rm -rf openocd


#iot-lab-ftdi-utils install

#(for M3 Nodes and Hikob IoT-LAB Gateway)
RUN git clone https://github.com/iot-lab/iot-lab-ftdi-utils/  &&\
    cd iot-lab-ftdi-utils &&\
    make &&\
    make install &&\
    cd .. && rm -rf iot-lab-ftdi-utils

#for all

RUN mkdir iot-lab-gateway
COPY ./iot-lab-gateway /setup_dir/iot-lab-gateway
RUN cd iot-lab-gateway &&\
    sudo python setup.py install &&\
    sudo python setup.py post_install
#problem from udev. Unable to interact with while in containers.

#test with SAMR21 config

 RUN mkdir -p /var/local/config/ &&\
     echo "M3" > /var/local/config/board_type &&\
     echo "no" > /var/local/config/control_node_type &&\
     echo "custom-123" > /var/local/config/hostname
#
# #Let's go
#
#CMD ["/etc/init.d/gateway-server-daemon","restart"]
#CMD ["/bin/bash"]
