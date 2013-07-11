#! /usr/share/env python
# -*- coding:utf-8 -*-

from setuptools import setup, Command
from setuptools.command.install import install

import os
from subprocess import Popen

from gateway_code import config


STATIC_FILES_PATH = config.STATIC_FILES_PATH
STATIC_FILES      = ['static/' + item for item in os.listdir('static')]
INIT_SCRIPT       = ('/etc/init.d/', ['bin/init_script/gateway-server-daemon'])
DATA              = [(STATIC_FILES_PATH, STATIC_FILES), INIT_SCRIPT]

SCRIPTS           = ['control_node_serial/control_node_serial_interface']
SCRIPTS          += ['bin/scripts/' + el for el in os.listdir('bin/scripts')]

# unload 'gateway_code.config'
# either it's not included in the coverage report...
import sys; del sys.modules['gateway_code.config']
#


def build_c_executable():
    saved_path = os.getcwd()
    os.chdir('control_node_serial')
    process = Popen(['make', 'realclean', 'all'])
    process.wait()

    os.chdir(saved_path)
    if process.returncode != 0:
        exit(0)


def setup_permissions():

    import stat
    # set init script executable
    init_script_path = INIT_SCRIPT[0] + os.path.basename(INIT_SCRIPT[1][0])
    mode = 0755
    os.chmod(init_script_path, mode)
    print "changing mode of %s to %d" % (init_script_path, mode)

    usermod_args = ['usermod', '-G', 'dialout', 'www-data']
    usermod = Popen(usermod_args)
    usermod.wait()
    print "%s: %d" % (' '.join(usermod_args), usermod.returncode)



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
        setup_permissions()


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

class Pep8(Command):
    user_options = []
    def initialize_options(self):
        self.exclude = None
    def finalize_options(self):
        pass
    def run(self):
        import pep8
        sys.argv = ['./pep8.py', 'gateway_code/']
        pep8._main()

INSTALL_REQUIRES  = ['argparse', 'bottle', 'paste', 'recordtype']
TESTS_REQUIRES    = ['nose>=1.0', 'pylint', 'nosexcover', 'mock', 'pep8']

setup(name='gateway_code',
        version='0.3',
        description='Linux Gateway code',
        author='SensLAB Team',
        author_email='admin@senslab.info',
        url='http://www.senslab.info',
        packages = ['gateway_code'],
        scripts = SCRIPTS,
        data_files = DATA,

        cmdclass = {'lint': Lint, 'install': Install, \
                'build_cn_serial': BuildSerial, 'pep8': Pep8},
        install_requires = INSTALL_REQUIRES,
        setup_requires = TESTS_REQUIRES + INSTALL_REQUIRES,
        )


