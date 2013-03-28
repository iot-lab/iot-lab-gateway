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



setup(name='gateway_code',
        version='0.2',
        description='Linux Gateway code',
        author='SensLAB Team',
        author_email='admin@senslab.info',
        url='http://www.senslab.info',
        packages = ['gateway_code'],
        cmdclass = {'lint': Lint,},

        install_requires = ['argparse', 'bottle', 'paste', 'pyserial'],
        setup_requires = ['nose>=1.0', 'pylint', 'nosexcover', 'mock'],
        )


