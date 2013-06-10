#! /usr/share/env python
# -*- coding:utf-8 -*-

from setuptools import setup, Command
from setuptools.command.install import install
import os
from subprocess import Popen



def build_c_executable():
    saved_path = os.getcwd()
    os.chdir('control_node_serial')

    process = Popen(['make', 'realclean', 'all'])
    process.wait()

    os.chdir(saved_path)
    if process.returncode != 0:
        exit(0)


class BuildSerial(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        build_c_executable()


class Install(install):
    def run(self):
        build_c_executable()
        install.run(self)


class Lint(Command):
    user_options = [
            ('report', 'r', "print errors and report"),
            ('outfile=', 'o', "duplicate output to file")]
    def initialize_options(self):
        self.report = False
        self.outfile = None

    def finalize_options(self):
        if self.report:
            self.report_option = ['--reports=y']
        else:
            self.report_option = ['--reports=n']

    def run(self):

        from pylint import lint
        lint_args = ['--rcfile=pylint.rc', '-f', 'parseable', 'gateway_code/']
        lint_args = self.report_option + lint_args

        # catch stdout to allow redirect to file
        if self.outfile is not None:
            from cStringIO import StringIO
            import sys
            sys.stdout = StringIO()

        lint.Run(lint_args, exit=False)

        # write pylint output
        if self.outfile is not None:
            my_output = sys.stdout.getvalue()
            # recover stdout
            sys.stdout = sys.__stdout__

            print my_output
            # duplicate output to file
            print 'Writing pylint output to file: %r' % self.outfile
            with open(self.outfile, 'w') as out:
                out.write(my_output)




INSTALL_REQUIRES = ['argparse', 'bottle', 'paste', 'pyserial', 'recordtype']
TESTS_REQUIRES = ['nose>=1.0', 'pylint', 'nosexcover', 'mock']

import os
from gateway_code import config
STATIC_FILES = ['static/' + item for item in os.listdir('static')]
STATIC_FILES_PATH  = config.STATIC_FILES_PATH

# unload 'gateway_code.config'
# either it's not included in the coverage report...
import sys; del sys.modules['gateway_code.config']

setup(name='gateway_code',
        version='0.22',
        description='Linux Gateway code',
        author='SensLAB Team',
        author_email='admin@senslab.info',
        url='http://www.senslab.info',
        packages = ['gateway_code'],
        scripts = ['flash_firmware', 'serial_redirection', 'gateway-rest-server', 'control_node_serial/control_node_serial_interface'],
        data_files = [(STATIC_FILES_PATH, STATIC_FILES)],

        cmdclass = {'lint': Lint, 'install': Install, 'build_cn_serial': BuildSerial},
        install_requires = INSTALL_REQUIRES,
        setup_requires = TESTS_REQUIRES + INSTALL_REQUIRES,
        )


