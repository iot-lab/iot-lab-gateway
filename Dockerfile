FROM ubuntu:14.04
MAINTAINER Cédric Roussel <cedric.roussel@inria.fr>

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

#MANDATORY
RUN apt-get update && \
    apt-get install -y git \
        python-dev \
        python-setuptools \
        socat && \
    apt-get clean

#openocd
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        libftdi-dev \
        libhidapi-dev \
        libusb-1.0-0-dev \
        autoconf \
        libsqlite3-dev \
        libpopt-dev \
        libxml2-dev \
        ruby \
        libtool \
        pkg-config && \
    apt-get clean

#AVR (arduino like)
RUN apt-get update && \
    apt-get install -y \
        avrdude && \
    apt-get clean

#To do http requests (to upload an experiment for instance)
RUN apt-get update && \
    apt-get install -y \
        curl && \
    apt-get clean

#Making a work directory to setup the gateway
RUN mkdir /setup_dir
WORKDIR /setup_dir

#liboml2 install
RUN mkdir /var/www && chown www-data:www-data /var/www

RUN apt-get update && \
    apt-get install -y \
        autoconf automake libtool gnulib libpopt-dev \
        libxml2 libsqlite3-dev pkg-config libxml2-utils && \
    apt-get clean

RUN git clone https://github.com/mytestbed/oml.git && \
    cd oml && \
    git checkout tags/v2.11.0 && \
    ./autogen.sh && \
    ./configure --disable-doc --disable-doxygen-doc --disable-doxygen-dot \ 
        --disable-android --disable-doxygen-html --disable-option-checking && \
    make && \
    sudo make install && \
    cd .. && rm -rf oml

#openocd install (for M3 and SAMR21)
RUN git clone https://github.com/ntfreak/openocd && \
    cd openocd && \
    git checkout v0.9.0 && \
    ./bootstrap && \
    ./configure  --enable-legacy-ft2232_libftdi --disable-ftdi2232 \
        --disable-ftd2xx --enable-cmsis-dap --enable-hidapi-libusb && \
    make && \
    sudo make install && \
    cd .. && rm -rf openocd

#openocd 0.10
RUN git clone https://github.com/ntfreak/openocd openocd10 && \
    cd openocd10 && \
    git checkout v0.10.0 && \
    ./bootstrap && \
    ./configure --prefix=/opt/openocd-0.10.0 --enable-cmsis-dap --enable-hidapi-libusb && \
    make && \
    sudo make install && \
    cd .. && rm -rf openocd10

#iot-lab-ftdi-utils install

#(for M3 Nodes and Hikob IoT-LAB Gateway)
RUN git clone https://github.com/iot-lab/iot-lab-ftdi-utils/  && \
    cd iot-lab-ftdi-utils && \
    make && \
    make install && \
    cd .. && rm -rf iot-lab-ftdi-utils

#for all

RUN rm -rf /setup_dir

WORKDIR /home

RUN mkdir iot-lab-gateway
COPY . /home/iot-lab-gateway/
RUN cd iot-lab-gateway && \
    python setup.py develop

#test with M3 config
RUN mkdir -p /var/local/config/ && \
    mkdir -p /iotlab/users/test && \
    chown www-data:www-data /iotlab/users/test

CMD ["/home/iot-lab-gateway/docker-gateway-rest-server"]
