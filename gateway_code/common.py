#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""
Common functions of the module
"""

import time


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
        _ = queue.get_nowait()


def wait_cond(timeout, value, fct, *args, **kwargs):
    """ Wait at max `timeout` for `fct(*args, **kwargs)` to return `value` """
    time_ref = time.time()
    while True:
        if value == fct(*args, **kwargs):
            return 0
        if time.time() > (time_ref + timeout):
            return 1
        time.sleep(0.1)
