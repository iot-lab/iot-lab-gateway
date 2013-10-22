#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""
Common functions of the module
"""


def empty_queue(queue):
    """
    Remove all items in Queue
    """
    while not queue.empty():
        _ = queue.get_nowait()
