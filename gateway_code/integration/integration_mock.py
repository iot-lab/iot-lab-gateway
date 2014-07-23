# -*- coding: utf-8 -*-
""" Implementation of common mocks for integration tests """

import os
import unittest
import mock
from mock import patch
import gateway_code.server_rest


class FileUpload(object):
    """ Bottle FileUpload class stub """
    files = {}

    def __init__(self, file_path):
        self.file = None
        self.filename = None
        self.name = None
        self.headers = None

        self.filename = os.path.basename(file_path)
        self._key, _ext = os.path.splitext(self.filename)

        try:
            self.name = {'.json': 'profile', '.elf': 'firmware'}[_ext]
        except KeyError:
            raise ValueError("Uknown file type %r: %r" % (_ext, file_path))

        self.file = open(file_path, 'rb')
        FileUpload.files[self._key] = self

    def rewind_file(self):
        """ Rewind at start position """
        self.file.seek(0)

    def close_file(self):
        """ Close the file object and remove it from class """
        self.file.close()
        FileUpload.files.pop(self._key)

    @staticmethod
    def rewind_all():
        """ Rewind all the files """
        for file_upload in FileUpload.files.values():
            file_upload.rewind_file()

    @staticmethod
    def close_all():
        """ Close all the files """
        for file_upload in FileUpload.files.values():
            file_upload.close_file()


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'
STATIC_DIR = CURRENT_DIR + 'static/'  # using the 'static' symbolic link
MOCK_FIRMWARES = {
    'idle': STATIC_DIR + 'idle.elf',
    'control_node': STATIC_DIR + 'control_node.elf',
    'm3_autotest': STATIC_DIR + 'm3_autotest.elf',
    'a8_autotest': STATIC_DIR + 'a8_autotest.elf'
    }


# pylint: disable=too-many-public-methods
class GatewayCodeMock(unittest.TestCase):
    """ gateway_code mock for integration tests  """

    @classmethod
    def setUpClass(cls):
        patch('gateway_code.config.STATIC_FILES_PATH', STATIC_DIR).start()
        patch(
            'gateway_code.autotest.open_a8_interface.config.STATIC_FILES_PATH',
            new=STATIC_DIR).start()

        patch('gateway_code.config.FIRMWARES', MOCK_FIRMWARES).start()
        # print measures
        patch('gateway_code.control_node_interface.TESTS_ARGS', ['-d']).start()

        g_m = gateway_code.server_rest.GatewayManager('.')
        g_m.setup()
        cls.app = gateway_code.server_rest.GatewayRest(g_m)

        # default files
        FileUpload(STATIC_DIR + 'control_node.elf')
        FileUpload(STATIC_DIR + 'idle.elf')
        FileUpload(STATIC_DIR + 'default_profile.json')
        # test specific files
        FileUpload(STATIC_DIR + 'm3_autotest.elf')
        FileUpload(CURRENT_DIR + 'profile.json')
        FileUpload(CURRENT_DIR + 'invalid_profile.json')
        FileUpload(CURRENT_DIR + 'invalid_profile_2.json')

    @classmethod
    def tearDownClass(cls):
        FileUpload.close_all()
        patch.stopall()

    def setUp(self):
        # get quick access to class attributes
        self.app = type(self).app

        self.request_patcher = patch('gateway_code.server_rest.request')
        self.request = self.request_patcher.start()
        self.request.query = mock.Mock(timeout='0')  # no timeout by default

        self.files = FileUpload.files
        FileUpload.rewind_all()

    def tearDown(self):
        self.request_patcher.stop()
        self.app.exp_stop()  # just in case, post error cleanup
