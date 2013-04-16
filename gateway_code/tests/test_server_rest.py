#! /usr/bin/env python

"""
Unit tests for server-rest
Complement the 'integration' tests
"""


from mock import patch

import gateway_code

class TestServerRest(object):
    """
    Cover functions uncovered by unit tests
    """

    @patch('gateway_code.server_rest.run')
    def test_main_function(self, run_mock):
        args = ['server_rest.py', 'localhost', '8080']
        gateway_code.server_rest.main(args)


