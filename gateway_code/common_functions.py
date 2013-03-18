#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""

Common functions file

"""



def num_arguments_required(func):
    """
    Returns the required number of argument to call ``func``

    :param func: the callable object to analyse
    :type func:  function or method
    :return:     number of arguments required to call 'func'
    :rtype:      int

    .. note:: a 'method' which has 'n' arguments requires 'n-1' arguments
              to be called as 'self' is automatically padded already provided

    """
    from inspect import getargspec, ismethod, isfunction
    if not (ismethod(func) or isfunction(func)):
        # other cases not tested
        raise ValueError, 'Required method or function'
    num = len(getargspec(func)[0])
    if ismethod(func):
        num -= 1 # 'self' argument is automatically passed
    return num

