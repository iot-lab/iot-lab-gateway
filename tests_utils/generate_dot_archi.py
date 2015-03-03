#! /usr/bin/env python
# -*- coding:utf-8 -*-

import os
from os.path import splitext, basename
import re
import sys


HEADER = '''
digraph g {

    graph [
        rankdir = "LR"
        splines = "polyline"
        ratio = 0.70
    ];
    node [
        fontsize = "16"
        shape = "record"
    ];

'''
FOOTER = '''}'''
NODE = '''    "%s" [
        label = "<f0> %s"
    ];
'''
NODE_LINK = '''    "%s" -> "%s"'''


SOURCE_FILES = ['gateway_code/' + py_file for py_file in
                os.listdir('gateway_code') if
                re.search('.py$', py_file) and py_file != '__init__.py']


print >> sys.stderr, SOURCE_FILES

nodes_assoc_list = []
i = 0
for current in SOURCE_FILES:

    # process each source file
    current_file = splitext(basename(current))[0]
    other_files = [splitext(basename(_f))[0] for _f in SOURCE_FILES]
    other_files.remove(current_file)

    # line containing 'import'
    import_lines = [line for line in open(current) if 'import' in line]

    for cur_line in import_lines:
        # for each dependency
        for dep_file in [deps for deps in other_files if deps in cur_line]:

            node_str = NODE_LINK % (current_file, dep_file)
            print >> sys.stderr, current_file, dep_file

            # lots of magic is done here to get the visually wanted result
            if dep_file in ('config', 'common'):
                node_str += ' [style=invis, constraint=false]'
            elif dep_file in ('gateway_logging', ):
                node_str += ' [constraint=false, minlen=4]'
            else:
                if ('gateway_validation', 'profile') != \
                        (current_file, dep_file):
                    node_str += ' [headport="w"]'

            nodes_assoc_list.append(node_str)


nodes_assoc_list.append(
    NODE_LINK % ('profile', 'open_node_validation_interface') +
    ' [style=invis]')
nodes_assoc_list.append(
    NODE_LINK % ('config', 'gateway_logging') + ' [style=invis]')

nodes_assoc_list.append(NODE_LINK % ('gateway_roomba', 'roomba/roomba.py'))
nodes_assoc_list.append(NODE_LINK % ('control_node_interface',
                                     'control_node_serial'))


print HEADER,
for file_path in SOURCE_FILES:
    file_name = splitext(basename(file_path))[0]
    print NODE % (file_name, file_name),

print '    "control_node_serial" [shape="Mrecord"];'
for node_ass in nodes_assoc_list:
    print node_ass

# Add clusters to be more readable
print """    subgraph cluster_config {
        config;
        common;
        style = invis;
    }
"""
print """    subgraph cluster_control_node {
        label = control_node;
        control_node_interface;
        protocol_cn;
        style = dotted;
    }
"""
print """    subgraph cluster_auto_tests {
        label = auto_tests;
        gateway_validation;
        open_node_validation_interface;
        open_a8_interface;
        style = dotted;
    }
"""
print """    subgraph cluster_subprocess {
        label = open_node;
        openocd_cmd;
        serial_redirection;
        style = dotted;
    }"""
print FOOTER,
