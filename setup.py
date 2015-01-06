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

Pylint and pep8 checker:

    python setup.py lint
    python setup.py pep8


"""

from setuptools import setup, Command, Extension
from setuptools.command.build_ext import build_ext
from setuptools.sandbox import run_setup

import sys
import os
import subprocess

from gateway_code import config
# pylint: disable=attribute-defined-outside-init
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods


# change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# error when putting the option in setup.cfg because of the '%' I think.
NOSE_LOGFORMAT = '%(asctime)s: %(name)s: %(levelname)s: %(message)s'
LOGGING_FORMAT_OPT = '--logging-format=%s' % NOSE_LOGFORMAT


STATIC_FILES_PATH = config.STATIC_FILES_PATH
STATIC_FILES = ['static/' + item for item in os.listdir('static')]
DATA = [(STATIC_FILES_PATH, STATIC_FILES)]

SCRIPTS = ['bin/scripts/' + el for el in os.listdir('bin/scripts')]
SCRIPTS += ['control_node_serial/' + config.CONTROL_NODE_SERIAL_INTERFACE]

EXT_MODULES = Extension(config.CONTROL_NODE_SERIAL_INTERFACE, [])

INSTALL_REQUIRES = ['argparse', 'bottle', 'paste', 'pyserial']
TESTS_REQUIRES = ['nose>=1.3', 'pylint', 'nosexcover', 'mock', 'pep8']

# unload 'gateway_code.config' module
# either it's not included in the coverage report...
try:
    del sys.modules['gateway_code.config']
except KeyError:
    pass


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
        """ Write data to stdout and file """
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        """ Flush the two files """
        self.file.flush()
        self.stdout.flush()

    def __enter__(self):
        pass

    def __exit__(self, _type, _value, _traceback):
        pass


def my_run_setup(setup_args, tee_stdout=os.devnull):
    """ Call 'run_setup' command and protect from SystemExit.
    If 'tee_stdout' provides file_path, tee the output to it """
    try:
        with _Tee(tee_stdout, 'w'):
            run_setup(sys.argv[0], setup_args)
    except SystemExit as err:
        print >> sys.stderr, '%r' % err
        return err[0]


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
            subprocess.check_call(['python', 'setup.py', 'install'])
        except subprocess.CalledProcessError as err:
            exit(err.returncode)
        self.post_install()

    @staticmethod
    def post_install():
        """ Install init.d script
        Add www-data user to dialout group """
        import shutil

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
    user_options = [('report', 'r', "print errors and report")]

    def initialize_options(self):
        self.report = False

    def finalize_options(self):
        self.report_opt = ['--reports=y'] if self.report else []

    def run(self):
        from pylint import lint
        lint_args = self.report_opt
        lint_args += ['--rcfile=pylint.rc', 'gateway_code/', 'setup.py']
        # 'roomba/'

        return lint.Run(lint_args, exit=False)


class Pep8(_EmptyCommand):
    """ Pep8 command """
    def run(self):
        import pep8

        sys.argv = ['./pep8.py', 'setup.py', 'gateway_code/', 'roomba/']
        # scripts don't have .py extension so list them one by one
        sys.argv += ['bin/scripts/' + f for f in os.listdir('bin/scripts')]
        return pep8._main()  # pylint: disable=W0212


class Tests(Command):
    """ Run unit tests, pylint and pep8 """
    user_options = [('tests=', None, "Run these tests (comma-separated-list)")]

    def initialize_options(self):
        self.tests = ''

    def finalize_options(self):
        self.tests_args = ['nosetests', LOGGING_FORMAT_OPT]
        self.tests_args += ['--tests=%s' % self.tests] if self.tests else []

    def run(self):
        my_run_setup(self.tests_args)
        my_run_setup(['lint'], 'pylint.out')
        my_run_setup(['pep8'], 'pep8.out')


class IntegrationTests(Command):
    """
    Run unit tests, pylint and pep8, and integration tests.
    Should be run on a gateway
    """
    user_options = [('stop', None, "Stop tests after a failed test"),
                    ('tests=', None, "Run these tests (comma-separated-list)")]

    def initialize_options(self):
        self.stop = False
        self.tests = ''

    def finalize_options(self):
        self.tests_args = ['run_integration_tests']
        self.tests_args += ['--tests=%s' % self.tests] if self.tests else []

        if self.stop:
            self.tests_args.append('--stop')

    def run(self):
        my_run_setup(self.tests_args)
        my_run_setup(['lint', '--report'], 'pylint.out')
        my_run_setup(['pep8'], 'pep8.out')


class OnlyIntegrationTests(Command):
    """ Run unit tests and integration tests.  Should be run on a gateway """
    user_options = [('stop', None, "Stop tests after a failed test"),
                    ('tests=', None, "Run these tests (comma-separated-list)")]

    def initialize_options(self):
        self.tests = ''
        self.stop = False

    def finalize_options(self):
        self.nose_args = ['nosetests', LOGGING_FORMAT_OPT,
                          '--xcoverage-file=%s_coverage.xml' % os.uname()[1],
                          '--xunit-file=%s_nosetests.xml' % os.uname()[1]]
        self.nose_args += ['--tests=%s' % self.tests] if self.tests else []
        if self.stop:
            self.nose_args.append('--stop')

    def run(self):
        args = ['python', 'setup.py']
        print >> sys.stderr, ' '.join(self.nose_args)

        env = os.environ.copy()
        env['PATH'] = './control_node_serial/:' + env['PATH']
        if 'www-data' != env['USER']:
            print >> sys.stderr, (
                "ERR: Run Integration tests as 'www-data':\n\n",
                "\tsu www-data -c 'python setup.py integration'\n"
            )
            exit(1)

        ret = subprocess.call(args + self.nose_args, env=env)
        return ret

setup(name='gateway_code',
      version='0.3',
      description='Linux Gateway code',
      author='SensLAB Team',
      author_email='admin@senslab.info',
      url='http://www.senslab.info',
      packages=['gateway_code', 'gateway_code.autotest', 'roomba'],
      scripts=SCRIPTS,
      data_files=DATA,

      ext_modules=[EXT_MODULES],

      cmdclass={
          'build_ext': BuildExt,
          'release': Release,
          'lint': Lint,
          'pep8': Pep8,
          'tests': Tests,
          'integration': IntegrationTests,
          'run_integration_tests': OnlyIntegrationTests,
      },
      install_requires=INSTALL_REQUIRES,
      setup_requires=TESTS_REQUIRES + INSTALL_REQUIRES)
