#! /usr/share/env python3
# -*- coding:utf-8 -*-

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


"""setup.py deployement script.

Install all the `gateway code` on a gateway

    python setup.py release

It runs the `install` command and the `post_install` procedure.

Tests commands:

    python setup.py nosetests
    python setup.py integration

Pylint and pep8 checker:

    python setup.py lint
    python setup.py pep8
"""

from setuptools import setup, Command, find_packages
from distutils.command.install import install

import sys
import os
import subprocess
import shutil
from glob import glob

PACKAGE = 'gateway_code'
# GPL compatible http://www.gnu.org/licenses/license-list.html#CeCILL
LICENSE = 'CeCILL v2.1'


def get_version(package):
    """Extract package version without importing file.

    Importing cause issues with coverage,
        (modules can be removed from sys.modules to prevent this)
    Importing __init__.py triggers importing rest and then requests too

    Inspired from pep8 setup.py
    """
    with open(os.path.join(package, '__init__.py')) as init_fd:
        for line in init_fd:
            if line.startswith('__version__'):
                return eval(line.split('=')[-1])  # pylint:disable=eval-used


SCRIPTS = glob('bin/scripts/*')

INSTALL_REQUIRES = ['argparse', 'bottle', 'paste', 'pyserial']
INSTALL_REQUIRES += ['pyelftools']
if sys.version_info[0] < 3:
    # Python3 backports of subprocess, support 'timeout' option
    INSTALL_REQUIRES += ['subprocess32']

UDEV_RULES = glob('bin/rules.d/*.rules')


def simple_command(function):
    """Return a simple command without options."""

    class SimpleCommand(Command):
        """Command without options."""

        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            """Run function with or without self argument."""
            try:
                execute(self, function, [self])
            except TypeError:
                execute(self, function)

    return SimpleCommand


def execute(self, function, args=()):
    """Run distutils execute function with args and auto-doc."""
    msg = function.__doc__.splitlines()[0]
    msg = 'running %s: %s' % (function.__name__, msg)
    self.execute(function, args, msg)


def post_install(self):
    """System configuration.

    * install init.d gateway server daemon script
    * install init.d gateway camera streamer daemon script
    * install init.d gateway rtl sdr daemon script
    * install udev rules files
    * Add www-data user to dialout group
    """
    execute(self, setup_initd_script, args=('gateway-server-daemon',))
    execute(self, udev_rules)
    execute(self, add_www_data_to_dialout)


def setup_initd_script(init_script):
    """Setup an init.d script."""
    update_rc_d_args = ['update-rc.d', init_script,
                        'start', '80', '2', '3', '4', '5', '.',
                        'stop', '20', '0', '1', '6', '.']
    shutil.copy('bin/init_script/' + init_script, '/etc/init.d/')
    os.chmod('/etc/init.d/' + init_script, 0o755)
    subprocess.check_call(update_rc_d_args)


def udev_rules():
    """Install udev rules files."""
    for rule in UDEV_RULES:
        shutil.copy(rule, '/etc/udev/rules.d/')
    subprocess.check_call(['udevadm', 'control', '--reload'])


def add_www_data_to_dialout():
    """Add `www-data` user to `dialout` group."""
    subprocess.check_call(['usermod', '-a', '-G', 'dialout', 'www-data'])


class Release(install):
    """Install and do the 'post installation' procedure too.

    Meant to be used directly on the gateways
    """

    def run(self):
        """Run `install` and `post_install`."""
        install.run(self)
        execute(self, post_install, [self])


PACKAGE_DATA = {
    'static': ['static/*'],
}

setup(name=PACKAGE,
      version=get_version(PACKAGE),
      description='Linux Gateway code',
      long_description="Linux Gateway code",
      author='IoT-Lab Team',
      author_email='admin@iot-lab.info',
      url='http://www.iot-lab.info',
      license=LICENSE,
      packages=find_packages(),

      scripts=SCRIPTS,
      include_package_data=True,
      package_data=PACKAGE_DATA,

      cmdclass={
          'release': Release,
          'post_install': simple_command(post_install),
          'udev_rules_install': simple_command(udev_rules),
      },
      install_requires=INSTALL_REQUIRES)
