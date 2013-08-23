#! /usr/share/env python
# -*- coding:utf-8 -*-

"""
setup.py deployement script

Install command:

    python setup.py install

Tests commands:

    python setup.py tests
    python setup.py integration
    python setup.py test_roomba

Pylint and pep8 checker:

    python setup.py lint
    python setup.py pep8


"""

from setuptools import setup, Command
from setuptools.command.install import install

import sys
import os
import re
import subprocess

from gateway_code import config
# Disable: R0904 - Too many public methods
# Disable: W0201 - Attribute '%s' defined outside __init__
# pylint: disable=R0904,W0201


STATIC_FILES_PATH = config.STATIC_FILES_PATH
STATIC_FILES = ['static/' + item for item in os.listdir('static')]
INIT_SCRIPT = ('/etc/init.d/', ['bin/init_script/gateway-server-daemon'])

DATA = [(STATIC_FILES_PATH, STATIC_FILES), INIT_SCRIPT]

SCRIPTS = ['control_node_serial/' + config.CONTROL_NODE_SERIAL_INTERFACE]
SCRIPTS += ['bin/scripts/' + el for el in os.listdir('bin/scripts')]

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

    def __enter__(self):
        pass

    def __exit__(self, _type, _value, _traceback):
        pass


def build_c_executable(debug_measures=0):
    """
    Build control node serial interface
    """
    saved_path = os.getcwd()
    os.chdir('control_node_serial')
    args = ['make', 'realclean', 'all']

    if debug_measures == 1:
        args.append("DEBUG_MEASURES=1")

    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        exit(1)
    os.chdir(saved_path)


def setup_permissions():
    """
    Setup file permissions on scripts
    Add www-data user to dialout group
    """
    # set init script executable
    init_script_path = INIT_SCRIPT[0] + os.path.basename(INIT_SCRIPT[1][0])
    mode = 0755
    os.chmod(init_script_path, mode)
    print "changing mode of %s to %d" % (init_script_path, mode)

    usermod_args = ['usermod', '-G', 'dialout', 'www-data']
    subprocess.check_call(usermod_args)


class BuildSerial(Command):
    """
    Build control node serial interface command
    """
    user_options = [('debug-measures', None, "print measures on stdout")]

    def initialize_options(self):
        self.debug_measures = 0

    def finalize_options(self):
        pass

    def run(self):
        build_c_executable(debug_measures=self.debug_measures)


class Install(install):
    """
    Install command

    * Build control node serial
    * install python code
    * correct file permissions
    """
    def run(self):
        build_c_executable()
        install.run(self)
        setup_permissions()


class Lint(Command):
    """
    Pylint command
    """
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


class Pep8(Command):
    """
    Pep8 command
    """
    user_options = [('outfile=', 'o', "duplicate output to file")]

    def initialize_options(self):
        self.exclude = None
        self.outfile = '/dev/null'

    def finalize_options(self):
        pass

    def run(self):
        import pep8
        sys.argv = ['./pep8.py', 'gateway_code/', 'roomba/']
        with _Tee(self.outfile, 'w'):
            pep8._main()  # pylint: disable=W0212


def _add_path_to_coverage_xml():
    """
    Add source path in coverage report,
    relativ to parent folder of git repository
    """
    current_folder = os.path.abspath('.')
    base_folder = os.path.abspath('../..') + '/'

    add_path = re.sub(base_folder, '', current_folder)
    match_path = os.path.basename(add_path)

    args = ['sed', '-i']
    args += ['/%s/ !s#filename="#&%s/#' % (match_path, add_path)]
    args += ['coverage.xml']

    subprocess.check_call(args)


class Tests(Command):
    """
    Run unit tests, pylint and pep8
    """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        args = ['python', 'setup.py']

        ret = 0
        try:
            ret = subprocess.call(args + ['nosetests', '--cover-html'])
            _add_path_to_coverage_xml()
            subprocess.call(args + ['lint', '-o', 'pylint.out'])
            subprocess.call(args + ['pep8', '-o', 'pep8.out'])
        except subprocess.CalledProcessError:
            exit(1)
        return ret


class TestsRoomba(Command):
    """
    Run roomba specific tests, should be run on a node with a robot conected
    """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        args = ['python', 'setup.py']

        try:
            subprocess.check_call(args + ['nosetests', '-i=*robot/*'])
            _add_path_to_coverage_xml()
        except subprocess.CalledProcessError:
            exit(1)


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

    @staticmethod
    def cleanup_workspace():
        """
        Remove old scripts output.
        Correct file permissions to be used with www-data
        """
        import stat
        # remove outfiles
        outfiles = ('coverage.xml', 'nosetests.xml', 'pylint.out', 'pep8.out')
        _ = [os.remove(_f) for _f in outfiles if os.path.exists(_f)]

        # chmod o+x script_dir
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mode = os.stat(script_dir).st_mode | stat.S_IWOTH
        os.chmod(script_dir, mode)

    @staticmethod
    def popen_as_user(user):
        """
        Allow running popen as another user.
        Also sets all groups user belongs to.
        """
        import pwd
        import grp

        pw_record = pwd.getpwnam(user)

        user_gid = pw_record.pw_gid
        user_uid = pw_record.pw_uid
        user_name = pw_record.pw_name
        user_home_dir = pw_record.pw_dir

        env = os.environ.copy()
        env['LOGNAME'] = user_name
        env['USER'] = user_name
        env['HOME'] = user_home_dir

        def preexec_set_uid_gid():
            """
            preexec fct run by popen to update user and groups
            """
            groups = [group.gr_gid for group in grp.getgrall()
                      if user in group.gr_mem]
            os.setgroups(groups)  # add all groups of user (for 'dialout')
            os.setgid(user_gid)
            os.setuid(user_uid)  # setuid after setgid to have permissions

        return preexec_set_uid_gid, env

    def run(self):
        args = ['python', 'setup.py']

        self.cleanup_workspace()
        ret = 0

        try:
            subprocess.check_call(args + ['build_cn_serial',
                                          '--debug-measures'])

            preexec_fn, env = self.popen_as_user('www-data')
            env['PATH'] = './control_node_serial/:%s' % env['PATH']

            _nose_args = args + ['nosetests', '-i=*integration/*']
            _nose_args += self.nose_args
            ret = subprocess.call(_nose_args, preexec_fn=preexec_fn, env=env)

            _add_path_to_coverage_xml()
            subprocess.call(args + ['lint', '--report', '-o', 'pylint.out'])
            subprocess.call(args + ['pep8', '-o', 'pep8.out'])
        except subprocess.CalledProcessError:
            exit(1)
        return ret


setup(name='gateway_code',
      version='0.3',
      description='Linux Gateway code',
      author='SensLAB Team',
      author_email='admin@senslab.info',
      url='http://www.senslab.info',
      packages=['gateway_code', 'roomba'],
      scripts=SCRIPTS,
      data_files=DATA,

      cmdclass={'install': Install,
                'build_cn_serial': BuildSerial,
                'lint': Lint,
                'pep8': Pep8,
                'tests': Tests,
                'integration': IntegrationTests,
                'test_roomba': TestsRoomba},
      install_requires=INSTALL_REQUIRES,
      setup_requires=TESTS_REQUIRES + INSTALL_REQUIRES,
      )
