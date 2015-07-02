#! /usr/bin/env python
# -*- coding:utf-8 -*-

""" Common functions of the module """

import os
import time
# http://code.activestate.com/recipes/\
#     577105-synchronization-decorator-for-class-methods/
# About the `functools.wrap` http://stackoverflow.com/a/309000/395687
from functools import wraps


def empty_queue(queue):
    """ Remove all items in Queue

    >>> import Queue
    >>> queue = Queue.Queue(0)
    >>> _ = [queue.put(i) for i in range(0, 10)]

    >>> queue.empty()
    False
    >>> empty_queue(queue)
    >>> queue.empty()
    True
    """
    while not queue.empty():
        queue.get_nowait()


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
            return False
        time.sleep(0.1)


def wait_tty(dev_tty, logger, timeout=0):
    """ Wait that tty is present """
    if wait_cond(timeout, True, os.path.exists, dev_tty):
        return 0
    logger.error('Error Open Node tty not visible: %s', dev_tty)
    return 1


def syncronous(tlockname):
    """A decorator to place an instance based lock around a method """
    def _synched(func):
        """ _decorated """
        @wraps(func)
        def _synchronizer(self, *args, **kwargs):
            """ _decorator """
            tlock = self.__getattribute__(tlockname)
            tlock.acquire()
            try:
                return func(self, *args, **kwargs)
            finally:
                tlock.release()
        return _synchronizer
    return _synched


def abspath(path):
    """ Return abspath of given `path` and check the file can be opened """
    abs_path = os.path.abspath(path)
    open(abs_path, 'rb').close()  # can be open by this user
    return abs_path
