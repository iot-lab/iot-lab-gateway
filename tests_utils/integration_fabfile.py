#! /usr/bin/env python
# -*- coding:utf-8 -*-


""" Allow running integration tests easily """

import os.path
from fabric.api import env, execute, run, runs_once, task
from fabric.context_managers import cd, settings
from fabric.contrib.project import rsync_project


EXCLUDE = ['.git', '.tox']
EXCLUDE += ['*egg-info', '*pyc', 'build', 'dist', 'cover', '.coverage']
EXCLUDE += ['*swp']
EXCLUDE += ['obj', 'results']
EXCLUDE += ['*.log', '*.out', '*.xml']
EXCLUDE += ['iotlab']  # test user measures directory

SCRIPT_DIR = os.path.dirname((__file__))
LOCAL = os.path.dirname(SCRIPT_DIR)
REMOTE = "/tmp/iot-lab-gateway"


SSH_CFG = os.path.join(SCRIPT_DIR, 'ssh_config')
env.ssh_config_path = SSH_CFG
env.use_ssh_config = True

# Required to re-add SSH_OPTS on the integration server
SSH_OPTS = '-F {0}'.format(SSH_CFG)

# Default to all targets
if not env.hosts:
    env.hosts = ['leonardo-00-ci', 'm3-00-ci', 'a8-00-ci', 'fox-00-ci']


@runs_once
@task
def upload():
    """ Upload sources as www-data:www-data """
    execute(_do_upload)


def _do_upload():
    """ Actually do the upload. """
    # 'runs_once' conflicts with multiple hosts, so call it with 'execute'
    extra_opts = " --delete-excluded"
    rsync_project(local_dir=LOCAL + '/', remote_dir=REMOTE, upload=True,
                  ssh_opts=SSH_OPTS, extra_opts=extra_opts,
                  exclude=EXCLUDE, delete=True)
    run('chown -R www-data:www-data {dir}'.format(dir=REMOTE))


@task
def download():
    """ Download tests results """
    extra_opts = (" --exclude='.tox' --exclude='*egg*'"
                  " --include='control_node_serial/'"
                  " --include='*/'"
                  " --include='*xml'"
                  " --exclude='*'")
    rsync_project(remote_dir=REMOTE + '/', local_dir=LOCAL, upload=False,
                  ssh_opts=SSH_OPTS, extra_opts=extra_opts)


def kill():
    """ Kill remote tests artifacts """
    with settings(warn_only=True):
        run('killall python socat control_node_serial_interface || true')


def safe_su(command, user='root'):
    """ Run a 'warn_only' su with command """
    with settings(warn_only=True):
        return run('su {user} -c "source /etc/profile; {cmd}"'.format(
            user=user, cmd=command))


@task()
def release():
    """ Release python package """
    execute(upload)
    execute(kill)
    with cd(REMOTE):
        run('source /etc/profile; python setup.py release')
    run('/etc/init.d/gateway-server-daemon restart', pty=False)


@task(default=True)
def python_test(*attrs):
    """ Execute python integration tests
    http://nose.readthedocs.org/en/latest/plugins/attrib.html

    :param attr: nosetets 'attr' option 'attribute=5,!other_attribute'
    """
    execute(upload)
    execute(kill)
    cmd = 'tox -e integration'
    if attrs:
        cmd += " -- --attr '%s'" % ','.join(attrs)
    with cd(REMOTE):
        ret = safe_su(cmd, user='www-data')
    execute(download)
    return ret.return_code


@task
def c_test():
    """ Execute `control_node_serial` tests """
    execute(upload)
    execute(kill)
    with cd(os.path.join(REMOTE, 'control_node_serial')):
        ret = safe_su('make realclean coverage', user='www-data')
    execute(download)
    return ret.return_code
