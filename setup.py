#! /usr/share/env python
# -*- coding:utf-8 -*-

from setuptools import setup, Command
from setuptools.command.install import install


class Install(install):
    def run(self):
        install.run(self)


class Lint(Command):
    user_options = [
            ('report', 'r', "print errors and report")]
    def initialize_options(self):
        self.report = False

    def finalize_options(self):
        if  self.report:
            self.report_option = ['--reports=y']
        else:
            self.report_option = ['--reports=n']

    def run(self):
        from pylint import lint
        lint_args = ['--rcfile=pylint.rc', '-f', 'parseable', 'gateway_code/']
        lint_args = self.report_option + lint_args
        # I didn't managed to catch the output of lint.Run function
        lint.Run(lint_args, exit=False)


INSTALL_REQUIRES = ['argparse', 'bottle', 'paste', 'pyserial']
TESTS_REQUIRES = ['nose>=1.0', 'pylint', 'nosexcover', 'mock']



setup(name='gateway_code',
        version='0.2',
        description='Linux Gateway code',
        author='SensLAB Team',
        author_email='admin@senslab.info',
        url='http://www.senslab.info',
        packages = ['gateway_code'],
        scripts = ['flash_firmware.py', 'serial_redirection.py', 'server_rest.py'],
        cmdclass = {'lint': Lint,},

        install_requires = INSTALL_REQUIRES,
        setup_requires = TESTS_REQUIRES + INSTALL_REQUIRES,
        )


