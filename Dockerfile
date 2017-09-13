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

#To do http requests (to upload an experiment for instance)
RUN apt-get update &&\
   apt-get install -y \
     curl &&\
   apt-get clean

#Making a work directory to setup the gateway
RUN mkdir /setup_dir
WORKDIR /setup_dir

#liboml2 install
RUN mkdir /var/www && chown www-data:www-data /var/www

RUN apt-get update &&\
   apt-get install -y\
     autoconf automake libtool gnulib libpopt-dev libxml2 libsqlite3-dev pkg-config libxml2-utils &&\
   apt-get clean

RUN git clone https://github.com/mytestbed/oml.git && \
    cd oml &&\
    git checkout tags/v2.11.0 &&\
    ./autogen.sh &&\
    ./configure --disable-doc --disable-doxygen-doc --disable-doxygen-dot --disable-android --disable-doxygen-html --disable-option-checking &&\
    make &&\
    sudo make install &&\
    cd .. && rm -rf oml

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

RUN rm -rf /setup_dir

WORKDIR /home

RUN mkdir iot-lab-gateway
COPY . /home/iot-lab-gateway/
RUN cd iot-lab-gateway && \
    python setup.py develop

#test with M3 config
 RUN mkdir -p /var/local/config/ &&\
     mkdir -p /iotlab/users/test &&\
     chown www-data:www-data /iotlab/users/test

CMD ["/home/iot-lab-gateway/docker-gateway-rest-server"]
