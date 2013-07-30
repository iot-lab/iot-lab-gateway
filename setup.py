#! /usr/share/env python
# -*- coding:utf-8 -*-

from setuptools import setup, Command
from setuptools.command.install import install

import os
from subprocess import Popen, check_call, CalledProcessError

from gateway_code import config


STATIC_FILES_PATH = config.STATIC_FILES_PATH
STATIC_FILES      = ['static/' + item for item in os.listdir('static')]
INIT_SCRIPT       = ('/etc/init.d/', ['bin/init_script/gateway-server-daemon'])
DATA              = [(STATIC_FILES_PATH, STATIC_FILES), INIT_SCRIPT]

SCRIPTS           = ['control_node_serial/control_node_serial_interface']
SCRIPTS          += ['bin/scripts/' + el for el in os.listdir('bin/scripts')]

INSTALL_REQUIRES  = ['argparse', 'bottle', 'paste', 'recordtype', 'pyserial']
TESTS_REQUIRES    = ['nose>=1.0', 'pylint', 'nosexcover', 'mock', 'pep8']

# unload 'gateway_code.config'
# either it's not included in the coverage report...
import sys; del sys.modules['gateway_code.config']


class _Tee(object):
    def __init__(self, name, mode):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self

    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

    def __enter__(self):
        pass

    def __exit__(self, _type, _value, _traceback):
        pass



def build_c_executable():
    saved_path = os.getcwd()
    os.chdir('control_node_serial')
    try:
        check_call(['make', 'realclean', 'all'])
    except CalledProcessError:
        exit(1)
    os.chdir(saved_path)

def setup_permissions():

    import stat
    # set init script executable
    init_script_path = INIT_SCRIPT[0] + os.path.basename(INIT_SCRIPT[1][0])
    mode = 0755
    os.chmod(init_script_path, mode)
    print "changing mode of %s to %d" % (init_script_path, mode)

    usermod_args = ['usermod', '-G', 'dialout', 'www-data']
    check_call(usermod_args)



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
        self.outfile = '/dev/null'

    def finalize_options(self):
        self.report_opt = ['--reports=y'] if self.report else ['--report=n']

    def run(self):
        from pylint import lint
        lint_args = self.report_opt
        lint_args += ['--rcfile=pylint.rc', '-f', 'parseable', 'gateway_code/']

        with _Tee(self.outfile, 'w'):
            lint.Run(lint_args, exit=False)


class Pep8(Command):
    user_options = [('outfile=', 'o', "duplicate output to file")]

    def initialize_options(self):
        self.exclude = None
        self.outfile = '/dev/null'

    def finalize_options(self):
        pass

    def run(self):
        import pep8
        sys.argv = ['./pep8.py', 'gateway_code/']
        with _Tee(self.outfile, 'w'):
            pep8._main()


class Tests(Command):
    user_options = []

    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        import subprocess, sys
        args = ['python', 'setup.py']

        try:
            ret = subprocess.check_call(args + ['nosetests', '--cover-html'])
            ret = subprocess.check_call(args + ['lint'])
            ret = subprocess.check_call(args + ['pep8'])
        except CalledProcessError:
            exit(1)



class IntegrationTests(Command):
    user_options = []

    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    @staticmethod
    def cleanup_workspace():
        import stat
        # remove outfiles
        for file in ('coverage.xml', 'nosetests.xml', 'pylint.out', 'pep8.out'):
            if os.path.exists(file):
                os.remove(file)

        # chmod o+x script_dir
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mode = os.stat(script_dir).st_mode | stat.S_IWOTH
        os.chmod(script_dir, mode)


    @staticmethod
    def popen_as_user(user):
        import pwd
        import grp

        pw_record = pwd.getpwnam(user)

        user_gid = pw_record.pw_gid
        user_uid = pw_record.pw_uid
        user_name = pw_record.pw_name
        user_home_dir = pw_record.pw_dir

        env = os.environ.copy()
        env[ 'HOME'     ]  = user_home_dir
        env[ 'LOGNAME'  ]  = user_name
        env[ 'USER'     ]  = user_name

        def preexec_set_uid_gid():
            groups = [group.gr_gid for group in grp.getgrall()
                      if user in group.gr_mem]
            os.setgroups(groups) # add all groups of user (for 'dialout')
            os.setgid(user_gid)
            os.setuid(user_uid) #setuid after setgid to have permissions

        return preexec_set_uid_gid, env


    def run(self):
        import subprocess, sys
        args = ['python', 'setup.py']

        self.cleanup_workspace()


        try:
            ret = subprocess.check_call(args + ['build_cn_serial'])

            preexec_fn, env = self.popen_as_user('www-data')
            env['PATH'] = './control_node_serial/:%s' % env['PATH']

            ret = subprocess.check_call(args +
                                        ['nosetests', '-i=*integration/*'],
                                        preexec_fn=preexec_fn, env=env)
            ret = subprocess.check_call(args + ['lint', '--report',
                                                '-o', 'pylint.out'])
            ret = subprocess.check_call(args + ['pep8', '-o', 'pep8.out'])
        except CalledProcessError:
            exit(1)



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
                'build_cn_serial': BuildSerial, 'pep8': Pep8,
                'tests': Tests,
                'integration': IntegrationTests},
        install_requires = INSTALL_REQUIRES,
        setup_requires = TESTS_REQUIRES + INSTALL_REQUIRES,
        )


