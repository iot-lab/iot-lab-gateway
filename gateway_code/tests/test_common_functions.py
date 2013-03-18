#! /usr/bin/env python
# -*- coding:utf-8 -*-

import mock

from gateway_code.common_functions import num_arguments_required
class Test_num_arguments_required(object):
    def test_valid_calls(self):
        class test:
            def method2(self, arg1, arg2):
                pass
            def method0(self):
                pass
        t = test()
        assert num_arguments_required(t.method2) == 2
        assert num_arguments_required(t.method0) == 0
        def function1(arg1):
            pass
        def function0():
            pass
        assert num_arguments_required(function1) == 1
        assert num_arguments_required(function0) == 0

        lambda_2 = (lambda x,y : 0)
        assert num_arguments_required(lambda_2) == 2


    def test_invalid_calls(self):

        # An object where it does not work: 'for example a mock'

        mock_test = mock.Mock()
        mock_test.method.side_effect = lambda_2 = (lambda x,y : 0)
        method = mock_test.method

        try:
            num_arguments_required(method)
        except ValueError:
            pass
        else:
            assert 0, 'No Value Error exception raised'
