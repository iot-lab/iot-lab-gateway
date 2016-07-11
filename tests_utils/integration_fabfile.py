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
EXCLUDE += ['*.log', '*.out', './*.xml']
EXCLUDE += ['iotlab']  # test user measures directory

EXCLUDE += ['control_node_serial/obj']
EXCLUDE += ['control_node_serial/tests/results/']
EXCLUDE += ['control_node_serial/tests/obj/']
EXCLUDE += ['control_node_serial/tests/bin/']

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
LOCAL = os.path.dirname(SCRIPT_DIR)
REMOTE = "/tmp/iot-lab-gateway"


SSH_CFG = os.path.join(SCRIPT_DIR, 'ssh_config')
env.ssh_config_path = SSH_CFG
env.use_ssh_config = True


env.roledefs = {
    'all-a8': ['a8-%d' % i for i in range(50, 65)],
    'all-ci': ['leonardo-00-ci', 'm3-00-ci', 'a8-00-ci', 'fox-00-ci'],
}

# Required to re-add SSH_OPTS on the integration server
SSH_OPTS = '-F {0}'.format(SSH_CFG)


def set_targets():
    """Set default roles, or use command line args."""
    if env.hosts or env.roles:
        return

    env.roles = ['all-ci']
    env.roles = ['all-a8']  # overwrite for moctar


set_targets()


def chown_www_data():
    """Set files as www_data."""
    run('chown -R www-data:www-data {dir}'.format(dir=REMOTE))


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
    chown_www_data()


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
        run('killall'
            ' python socat control_node_serial_interface openocd'
            ' || true')


def safe_su(command, user='root'):
    """ Run a 'warn_only' su with command """
    with settings(warn_only=True):
        return run('su {user} -c "source /etc/profile; {cmd}"'.format(
            user=user, cmd=command))


@task
def server_restart():
    """Restart Gateway server."""
    return run('/etc/init.d/gateway-server-daemon restart', pty=False)


@task
def release():
    """Release python package."""
    upload()
    kill()
    with cd(REMOTE):
        run('source /etc/profile; python setup.py release')
    server_restart()


@task
@runs_once
def deploy():
    """Deploy newer server on test a8 nodes."""
    with settings(roles=[], hosts=['a8-50']):
        release()
    execute(server_restart)


@task
def status():
    """Run gateway status command."""
    run('curl -s http://localhost:8080/status')


@task
def post_install():
    """PostInstall python package."""
    upload()
    kill()
    with cd(REMOTE):
        run('source /etc/profile; python setup.py post_install')
    server_restart()


@task
def udev_rules_install():
    """Install udev rules."""
    upload()
    with cd(REMOTE):
        run('source /etc/profile; python setup.py udev_rules_install')


@task(default=True)
def python_test(*attrs):
    """ Execute python integration tests
    http://nose.readthedocs.org/en/latest/plugins/attrib.html

    :param attr: nosetets 'attr' option 'attribute=5,!other_attribute'
    """
    upload()
    kill()
    udev_rules_install()
    chown_www_data()
    ret = tox_call('integration', 'www-data', *attrs)
    download()
    return ret


@runs_once
@task
def c_test():
    """ Execute `control_node_serial` tests """
    upload()
    kill()
    ret = tox_call('control_node_serial', 'www-data')
    download()
    return ret


def tox_call(cmd, user, *attrs):
    """ Call given tox command as user with attributes """
    cmd = 'tox -e %s' % cmd
    if attrs:
        cmd += " -- --attr '%s'" % ','.join(attrs)
    with cd(REMOTE):
        ret = safe_su(cmd, user=user)
    return ret.return_code


@task
def uptime():
    """Simply run 'uptime' command."""
    run('uptime')


@task
@runs_once
def all():
    """Execute python tests, c tests and restart Gateway Server."""
    # Only upload once for all hosts
    upload()
    # Runs_once combined with 'execute'
    # to only execute once per host but with c_test run at the end
    execute(python_test)
    execute(c_test)
    execute(server_restart)
