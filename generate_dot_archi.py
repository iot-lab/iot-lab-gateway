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
    ];
    node [
        fontsize = "16"
        shape = "ellipse"
    ];
    edge [
    ];

'''
FOOTER = '''
}
'''

NODE  = '''    "%s" [
        label = "<f0> %s | <f1>"
        shape = "record"
    ];
'''
NODE_LINK  = '''    "%s":f0 -> "%s":f0 [
        id = %i
    ];
'''


source_files = ['gateway_code/' + python_file for python_file in os.listdir('gateway_code') if re.search('.py$', python_file) and python_file != '__init__.py']




print >> sys.stderr, source_files

nodes_assoc_list = []
i = 0
for current in source_files:
    current_name = splitext(basename(current))[0]
    other_names =  [splitext(basename(_f))[0] for _f in source_files if _f != current ]

    for cur_line in open(current):
        if 'import' in cur_line:
            for other in other_names:
                if other in cur_line:
                    print >> sys.stderr, current_name, other
                    node_str = NODE_LINK % (current_name, other, i)
                    nodes_assoc_list.append(node_str)
                    i += 1



print HEADER,
for file_path in source_files:
    file_name = splitext(basename(file_path))[0]
    print NODE % (file_name, file_name),
for node_ass in nodes_assoc_list:
    print node_ass,
print FOOTER,



