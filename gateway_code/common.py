#! /usr/bin/env python
# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


""" Common functions of the module """

import os
import time
import errno
# pylint: disable=unused-import
import queue  # noqa

# http://code.activestate.com/recipes/\
#     577105-synchronization-decorator-for-class-methods/
# About `functools.wraps` http://stackoverflow.com/a/309000/395687
import functools

import logging
LOGGER = logging.getLogger('gateway_code')


def logger_call(msg, log_lvl='info', err_lvl='warning'):
    """ Decorator to wrap a function with logs

    Print a message before calling the function and an error message in case of
    non zero return value.

    :param msg: message used in logs messages
    :param log_lvl: Logger level for info message
    :param err_lvl: Logger level for error message
    """

    log_msg = getattr(LOGGER, log_lvl)
    log_err = getattr(LOGGER, err_lvl)

    def _wrap(func):
        """ Decorator implementation """
        @functools.wraps(func)
        def _wrapped_f(*args, **kwargs):
            """ Function wrapped with logs """
            log_msg(msg)
            ret = func(*args, **kwargs)
            if ret:
                log_err("%s FAILED: ret = %d", msg, ret)
            return ret

        return _wrapped_f
    return _wrap


def empty_queue(my_queue):
    """ Remove all items in Queue

    >>> my_queue = queue.Queue(0)
    >>> _ = [my_queue.put(i) for i in range(0, 10)]

    >>> my_queue.empty()
    False
    >>> empty_queue(my_queue)
    >>> my_queue.empty()
    True
    """
    while not my_queue.empty():
        my_queue.get_nowait()


def wait_cond(timeout, value, fct, *args, **kwargs):
    """ Wait at max `timeout` for `fct(*args, **kwargs)` to return `value`
    :return: True if fct has returned `value` before timeout False otherwise.
    :rtype: bool
    """
    time_ref = time.time()
    while True:
        if value == fct(*args, **kwargs):
            return True
        if time.time() > (time_ref + timeout):
            break
        time.sleep(0.1)
    return False


# The embedded need some time to detect the tty
# At least of 1.33 seconds has been (so ~ x2)
TTY_DETECT_TIME = 3


def wait_tty(dev_tty, logger, timeout=TTY_DETECT_TIME):
    """ Wait that tty is present """
    if wait_cond(timeout, True, os.path.exists, dev_tty):
        return 0
    logger.error('Error Open Node tty not visible: %s', dev_tty)
    return 1


def wait_no_tty(dev_tty, timeout=TTY_DETECT_TIME):
    """ Wait until `dev_tty` is not present """
    ret = wait_cond(timeout, False, os.path.exists, dev_tty)
    return 0 if ret else 1


def synchronous(tlockname):
    """A decorator to place an instance based lock around a method """
    def _wrap(func):
        """Decorator implementation."""
        @functools.wraps(func)
        def _wrapped_f(self, *args, **kwargs):
            """ Function protected by 'rlock' """
            tlock = self.__getattribute__(tlockname)
            if not tlock.acquire(blocking=False):
                err = errno.EWOULDBLOCK
                name = self.__class__.__name__
                raise EnvironmentError(err, os.strerror(err), name)

            try:
                return func(self, *args, **kwargs)
            finally:
                tlock.release()
        return _wrapped_f
    return _wrap


def abspath(path):
    """ Return abspath of given `path` and check the file can be opened """
    abs_path = os.path.abspath(path)
    open(abs_path, 'rb').close()  # can be open by this user
    return abs_path


def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value.

    http://pingfive.typepad.com/blog/2010/04/deep-getattr-python-function.html
    """
    return functools.reduce(getattr, attr.split('.'), obj)


def object_attr_has(obj, features_attr, required_list):
    """Return if obj.features_attr has required_list members in it."""
    required = set(required_list)
    available = set(deepgetattr(obj, features_attr))
    return required.issubset(available)


def class_attr_has(features_attr, required_list):
    """Only run tests if required `commands` are in self.features_attr."""

    def _wrap(func):
        """ Decorator implementation """
        @functools.wraps(func)
        def _wrapped_f(self, *args, **kwargs):
            """ Function wrapped with test """
            has_required = object_attr_has(self, features_attr, required_list)
            if has_required:
                return func(self, *args, **kwargs)
            return 0
        return _wrapped_f
    return _wrap


def booleanize(value):
    # insp. https://stackoverflow.com/q/11641689
    """Convert a representation of truth to a boolean value
    If already a boolean, return it
    True values are 'y', 'yes', 't', 'true', 'on', '1' and 1;
    False values are 'n', 'no', 'f', 'false', 'off', '0', 0 and None.
    Raises ValueError if 'value' is anything else.

    >>> booleanize(False)
    False
    >>> booleanize('n')
    False
    >>> booleanize('no')
    False
    >>> booleanize('false')
    False
    >>> booleanize('False')
    False
    >>> booleanize('off')
    False
    >>> booleanize('0')
    False
    >>> booleanize(0)
    False
    >>> booleanize(None)
    False
    >>> booleanize(True)
    True
    >>> booleanize('y')
    True
    >>> booleanize('yes')
    True
    >>> booleanize('true')
    True
    >>> booleanize('True')
    True
    >>> booleanize('on')
    True
    >>> booleanize('1')
    True
    >>> booleanize(1)
    True
    >>> booleanize([])
    Traceback (most recent call last):
        ...
    ValueError: invalid value '[]'
    >>> booleanize({})
    Traceback (most recent call last):
        ...
    ValueError: invalid value '{}'
    """

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        value = value.lower()

    if value in ('y', 'yes', 't', 'true', 'on', '1', 1):
        return True

    if value in ('n', 'no', 'f', 'false', 'off', '0', 0, None):
        return False

    raise ValueError("invalid value '{}'".format(value))
