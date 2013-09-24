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
    ];
    node [
        fontsize = "16"
        shape = "record"
    ];

'''
FOOTER = '''
}
'''

NODE  = '''    "%s" [
        label = "<f0> %s"
    ];
'''
NODE_LINK  = '''    "%s" -> "%s"'''


source_files = ['gateway_code/' + python_file for python_file in os.listdir('gateway_code') if re.search('.py$', python_file) and python_file != '__init__.py']




print >> sys.stderr, source_files

nodes_assoc_list = []
i = 0
for current in source_files:
    current_file = splitext(basename(current))[0]
    other_files =  [splitext(basename(_f))[0] for _f in source_files if _f != current ]

    for cur_line in open(current):
        if 'import' in cur_line:
            # for each dependency
            for dep_file in [deps for deps in other_files if deps in cur_line]:
                print >> sys.stderr, current_file, dep_file
                node_str = NODE_LINK % (current_file, dep_file)
                if dep_file in ('config', 'common'):
                    node_str += ' [style=dotted]'
                nodes_assoc_list.append(node_str)

nodes_assoc_list.append(NODE_LINK % ('common', 'config') + ' [style=invis]')
nodes_assoc_list.append(NODE_LINK % ('config', 'common') + ' [style=invis]')


print HEADER,
for file_path in source_files:
    file_name = splitext(basename(file_path))[0]
    print NODE % (file_name, file_name),
for node_ass in nodes_assoc_list:
    print node_ass
print FOOTER,



