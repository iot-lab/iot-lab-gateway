#! /usr/share/env python
# -*- coding:utf-8 -*-

"""
setup.py deployement script

Install all the `gateway code` on a gateway

        python setup.py release

It runs the `install` command and the `post_install` procedure.

Tests commands:

    python setup.py tests
    python setup.py integration
    python setup.py test_roomba

Pylint and pep8 checker:

    python setup.py lint
    python setup.py pep8


"""

from setuptools import setup, Command, Extension
from setuptools.command.build_ext import build_ext

import sys
from sys import stderr
import os
import re
import subprocess

from gateway_code import config
# Disable: R0904 - Too many public methods
# Disable: W0201 - Attribute '%s' defined outside __init__
# Disable: C0111 - Missing docstring (for Command methods)
# Disable: R0201 - Method could be a function (Command.run)
# Disable: W0232 - Class has no __init__ method
# pylint: disable=R0904,W0201,C0111,R0201,W0232


# change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))


STATIC_FILES_PATH = config.STATIC_FILES_PATH
STATIC_FILES = ['static/' + item for item in os.listdir('static')]
DATA = [(STATIC_FILES_PATH, STATIC_FILES)]

SCRIPTS = ['bin/scripts/' + el for el in os.listdir('bin/scripts')]

EXT_MODULES = Extension(config.CONTROL_NODE_SERIAL_INTERFACE, [])

INSTALL_REQUIRES = ['argparse', 'bottle', 'paste', 'recordtype', 'pyserial']
TESTS_REQUIRES = ['nose>=1.0', 'pylint', 'nosexcover', 'mock', 'pep8']

# unload 'gateway_code.config' module
# either it's not included in the coverage report...
del sys.modules['gateway_code.config']


class _Tee(object):
    """
    File object which mimic 'tee' linux command behaviour
    It writes to file_path and stdout
    """
    def __init__(self, file_path, mode):
        self.file = open(file_path, mode)
        self.stdout = sys.stdout
        sys.stdout = self

    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        """
        Write data to stdout and file
        """
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.file.flush()
        self.stdout.flush()

    def __enter__(self):
        pass

    def __exit__(self, _type, _value, _traceback):
        pass


class _EmptyCommand(Command):
    """ An empty command doing nothing used for inheritance"""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pass


class BuildExt(build_ext):
    """ Overwrite build_ext to build control node serial """

    def run(self):
        """ Build control node serial interface """
        args = ['make', '-C', 'control_node_serial', 'realclean', 'all']
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError as err:
            exit(err.returncode)


class Release(_EmptyCommand):
    """ Install and do the 'post installation' procedure too.
    Meant to be used directly on the gateways """

    def run(self):
        try:
            subprocess.call(['python', 'setup.py', 'install'])
        except subprocess.CalledProcessError as err:
            exit(err.returncode)
        self.post_install()

    @staticmethod
    def post_install():
        """ Install init.d script
        Add www-data user to dialout group """
        import shutil
        print >> sys.stderr, 'running post_install'

        # setup init script
        init_script = 'gateway-server-daemon'
        update_rc_d_args = ['update-rc.d', init_script,
                            'start', '80', '2', '3', '4', '5', '.',
                            'stop', '20', '0', '1', '6', '.']
        shutil.copy('bin/init_script/' + init_script, '/etc/init.d/')
        os.chmod('/etc/init.d/' + init_script, 0755)
        subprocess.check_call(update_rc_d_args)

        #  add `www-data` user to `dialout` group
        subprocess.check_call(['usermod', '-a', '-G', 'dialout', 'www-data'])


class Lint(Command):
    """ Pylint command """
    user_options = [
        ('report', 'r', "print errors and report"),
        ('outfile=', 'o', "duplicate output to file")]

    def initialize_options(self):
        self.report = False
        self.outfile = '/dev/null'

    def finalize_options(self):
        self.report_opt = ['--reports=y'] if self.report else []

    def run(self):
        from pylint import lint
        lint_args = self.report_opt
        lint_args += ['--rcfile=pylint.rc', 'gateway_code/', 'roomba/',
                      'setup.py']

        with _Tee(self.outfile, 'w'):
            lint.Run(lint_args, exit=False)


class Pep8(_EmptyCommand):
    """ Pep8 command """
    user_options = [('outfile=', 'o', "duplicate output to file")]

    def initialize_options(self):
        self.exclude = None
        self.outfile = '/dev/null'

    def run(self):
        import pep8
        sys.argv = ['./pep8.py', 'gateway_code/', 'roomba/']
        with _Tee(self.outfile, 'w'):
            pep8._main()  # pylint: disable=W0212


def _add_path_to_coverage_xml():
    """ Add source path in coverage report,
    relativ to parent folder of git repository """
    current_folder = os.path.abspath('.')
    base_folder = os.path.abspath('../..') + '/'

    add_path = re.sub(base_folder, '', current_folder)
    match_path = os.path.basename(add_path)

    args = ['sed', '-i']
    args += ['/%s/ !s#filename="#&%s/#' % (match_path, add_path)]
    args += ['coverage.xml']

    subprocess.check_call(args)


class Tests(_EmptyCommand):
    """ Run unit tests, pylint and pep8 """
    def run(self):
        args = ['python', 'setup.py']
        try:
            ret = subprocess.call(args + ['nosetests', '--cover-html'])
            _add_path_to_coverage_xml()
            subprocess.call(args + ['lint', '-o', 'pylint.out'])
            subprocess.call(args + ['pep8', '-o', 'pep8.out'])
            return ret
        except subprocess.CalledProcessError as err:
            exit(err.returncode)


class TestsRoomba(_EmptyCommand):
    """
    Run roomba specific tests, should be run on a node with a robot conected
    """
    def run(self):
        args = ['python', 'setup.py']
        try:
            subprocess.check_call(args + ['nosetests', '-i=*robot/*'])
            _add_path_to_coverage_xml()
        except subprocess.CalledProcessError as err:
            exit(err.returncode)


class IntegrationTests(Command):
    """
    Run unit tests, pylint and pep8, and integration tests.
    Should be run on a gateway
    """
    user_options = [('stop', None, "Stop tests after a failed test")]

    def initialize_options(self):
        self.stop = False

    def finalize_options(self):
        self.nose_args = []
        if self.stop:
            self.nose_args += ['--stop']

    def run(self):
        args = ['python', 'setup.py']

        env = os.environ.copy()
        if 'www-data' != env['USER']:
            stderr.write("ERR: Run Integration tests as 'www-data':\n")
            stderr.write("\nsu www-data -c 'python setup.py integration'\n")
            exit(1)

        try:
            self.cleanup_workspace()

            env['PATH'] = './control_node_serial/:' + env['PATH']
            ret = subprocess.call(
                args + ['nosetests', '-i=*integration/*'] + self.nose_args,
                env=env)
            _add_path_to_coverage_xml()

            subprocess.call(args + ['lint', '--report', '-o', 'pylint.out'])
            subprocess.call(args + ['pep8', '-o', 'pep8.out'])
            return ret
        except subprocess.CalledProcessError:
            exit(1)

    @staticmethod
    def cleanup_workspace():
        """ Remove old scripts output.  """
        outfiles = ('coverage.xml', 'nosetests.xml', 'pylint.out', 'pep8.out')
        for _file in outfiles:
            try:
                os.remove(_file)
            except OSError:
                pass


setup(name='gateway_code',
      version='0.3',
      description='Linux Gateway code',
      author='SensLAB Team',
      author_email='admin@senslab.info',
      url='http://www.senslab.info',
      packages=['gateway_code', 'roomba'],
      scripts=SCRIPTS,
      data_files=DATA,

      ext_modules=[EXT_MODULES],

      cmdclass={'build_ext': BuildExt,
                'release': Release,
                'lint': Lint,
                'pep8': Pep8,
                'tests': Tests,
                'integration': IntegrationTests,
                'test_roomba': TestsRoomba},
      install_requires=INSTALL_REQUIRES,
      setup_requires=TESTS_REQUIRES + INSTALL_REQUIRES,
      )
