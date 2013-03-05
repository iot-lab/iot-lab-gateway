#! /usr/share/env python

from setuptools import setup, Command
from setuptools.command.install import install

def __check_dependencies():
    try:
        __import__('argparse')
    except ImportError, e:
        print 'Dependencies error: %s' % e
        exit(1)


class Install(install):
    def run(self):
        __check_dependencies()
        install.run(self)


class Lint(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        from pylint import lint
        lint_args = ['-f', 'parseable', 'gateway_code/']
        # I didn't managed to catch the output of lint.Run function
        lint.Run(lint_args, exit=False)



setup(name='gateway_code',
        version='0.1',
        description='Linux Gateway code',
        author='SensLAB Team',
        author_email='admin@senslab.info',
        url='http://www.senslab.info',
        packages = ['gateway_code'],
        cmdclass = {'lint': Lint,},

        install_requires = ['argparse'],
        setup_requires = ['nose>=1.0', 'pylint', 'nosexcover'],
        )


