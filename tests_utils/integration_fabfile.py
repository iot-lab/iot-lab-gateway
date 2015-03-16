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

SCRIPT_DIR = os.path.dirname((__file__))
LOCAL = os.path.dirname(SCRIPT_DIR)
REMOTE = "/tmp/iot-lab-gateway"


SSH_CFG = os.path.join(SCRIPT_DIR, 'ssh_config')
env.ssh_config_path = SSH_CFG
env.use_ssh_config = True

# Required to re-add SSH_OPTS on the integration server
SSH_OPTS = '-F {0}'.format(SSH_CFG)


@runs_once
@task
def upload():
    """ Upload sources as www-data:www-data """
    rsync_project(local_dir=LOCAL + '/', remote_dir=REMOTE, upload=True,
                  ssh_opts=SSH_OPTS, exclude=EXCLUDE, delete=True)
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


@task(default=True)
def python_test():
    """ Execute python integration tests """
    execute(upload)
    execute(kill)
    with cd(REMOTE):
        ret = safe_su('tox -e integration', user='www-data')
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
