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

"""Validate elf target class and machine."""

import logging

from elftools.elf.constants import SH_FLAGS
from elftools.elf.elffile import ELFFile
import elftools.common.exceptions

LOGGER = logging.getLogger('gateway_code')

TYPE_EXECUTABLE = 'ET_EXEC'


def elf_target(filepath):
    """Returns elf (class, machine) tuple.

    :raises: ValueError if file is not an executable elf file.
    """
    try:
        with open(filepath, 'rb') as _file:
            elffile = ELFFile(_file)
    except elftools.common.exceptions.ELFError:
        raise ValueError('Not a valid elf file')

    # Type
    e_type = elffile.header['e_type']
    # Class
    e_class = elffile.header['e_ident']['EI_CLASS']
    # Machine
    e_machine = elffile.header['e_machine']

    if e_type != TYPE_EXECUTABLE:
        raise ValueError('Not an executable elf file: %s' % e_type)

    return e_class, e_machine


def is_compatible_with_node(firmware_path, node_class):
    """Test if firmware at `firmware` matches `node_class` required target."""
    # Ignore None
    if firmware_path is None:
        return True

    node_elf_target = tuple(node_class.ELF_TARGET)
    try:
        return elf_target(firmware_path) == node_elf_target
    except ValueError as err:
        LOGGER.warning('Invalid firmware: %s', err)
        return False


def get_elf_load_addr(firmware_path):
    """ Read the load offset for the given elf """
    with open(firmware_path, 'rb') as firmware_file:
        elf_file = ELFFile(firmware_file)
        for section in elf_file.iter_sections():
            sh_flags = section['sh_flags']
            if sh_flags & SH_FLAGS.SHF_EXECINSTR:
                return section['sh_addr']


def main():
    """Read class and machine for given firmware."""
    import sys
    print elf_target(sys.argv[1])


if __name__ == '__main__':
    main()
