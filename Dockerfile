FROM ubuntu:20.04
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

ENV DEBIAN_FRONTEND noninteractive

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN apt-get update && \
    apt-get install -y git \
        # MANDATORY
        python3-dev \
        python3-setuptools \
        socat \
        # openocd
        build-essential \
        libftdi-dev \
        libhidapi-dev \
        libusb-1.0-0-dev \
        libudev-dev \
        autoconf \
        libsqlite3-dev \
        libpopt-dev \
        libxml2-dev \
        ruby \
        libtool \
        pkg-config \
        # To do http requests (to upload an experiment for instance)
        curl \
        # liboml2 install
        autoconf \
        automake \
        libtool \
        gnulib \
        libpopt-dev \
        libxml2 \
        libsqlite3-dev \
        pkg-config \
        libxml2-utils \
        # cc2538 for firefly
        python3-pip \
        binutils \
        # AVR (arduino like)
        avrdude \
        avarice \
        && \
    apt-get clean

#liboml2 install
RUN mkdir /var/www && chown www-data:www-data /var/www

#openocd 0.10
RUN git clone https://github.com/ntfreak/openocd openocd10 && \
    cd openocd10 && \
    git checkout v0.10.0 && \
    ./bootstrap && \
    ./configure --enable-cmsis-dap --enable-hidapi-libusb --disable-werror && \
    make && \
    make install && \
    cd .. && rm -rf openocd10

#openocd dev
RUN git clone https://github.com/ntfreak/openocd openocd-dev && \
    cd openocd-dev && \
    git checkout 7c88e76a76588fa0e3ab645adfc46e8baff6a3e4 && \
    ./bootstrap && \
    ./configure --prefix=/opt/openocd-dev --enable-cmsis-dap --enable-hidapi-libusb && \
    make && \
    make install && \
    cd .. && rm -rf openocd-dev

# edbg
RUN git clone https://github.com/ataradov/edbg && \
    cd edbg && \
    git checkout 80c50d03aac831f87f513a5d5455df1286bcb540 && \
    make all && \
    install -m 755 edbg /usr/bin && \
    cd .. && rm -rf edbg

#iot-lab-ftdi-utils install

#(for M3 Nodes and Hikob IoT-LAB Gateway)
RUN git clone https://github.com/iot-lab/iot-lab-ftdi-utils/  && \
    cd iot-lab-ftdi-utils && \
    make && \
    make install && \
    cd .. && rm -rf iot-lab-ftdi-utils

# cc2538 for firefly
RUN git clone https://github.com/JelmerT/cc2538-bsl && \
    cp cc2538-bsl/cc2538-bsl.py /usr/bin/. && \
    pip3 install intelhex

RUN git clone https://github.com/iot-lab/oml.git -b iotlab && \
    cd oml && \
    ./autogen.sh && \
    ./configure --disable-doc --disable-doxygen-doc --disable-doxygen-dot \
        --disable-android --disable-doxygen-html --disable-option-checking && \
    make && \
    make install && \
    cd .. && rm -rf oml

# control_node_serial
RUN git clone https://github.com/iot-lab/control_node_serial && \
    make -C control_node_serial && \
    cp control_node_serial/control_node_serial_interface /usr/bin/. && \
    rm -rf control_node_serial

# pycom-utils
RUN git clone https://github.com/iot-lab/pycom-utils && \
    mkdir -p /usr/local/share/pycom/eps32/tools/fw_updater && \
    cd pycom-utils && \
    cp *.py /usr/local/share/pycom/eps32/tools/fw_updater/

WORKDIR /setup_dir
COPY . /setup_dir/
RUN python3 setup.py install
RUN rm -r /setup_dir

#test with M3 config
RUN mkdir -p /var/local/config/ && \
    mkdir -p /iotlab/users/test && \
    chown www-data:www-data /iotlab/users/test

CMD ["gateway-rest-server", "0.0.0.0", "8080", "--log-stdout", "--reloader"]
