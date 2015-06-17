#! /usr/bin/env python
# -*- coding:utf-8 -*-

import os.path
from subprocess import check_output, check_call
import logging


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
FOOTER = '}'
NODE = '''    "%s" [
        label = "<f0> %s"
    ];
'''
NODE_LINK = '    "%s" -> "%s"'


CLUSTER_FMT = """
    subgraph cluster_%s {
        label = %s;
        %s
        style = dotted;
    }
"""


def mod_name(path):
    return os.path.splitext(os.path.basename(path))[0]


def extract_associations(files):
    modules = {mod_name(_f) for _f in files}

    associations = []

    for current in files:

        # process each source file
        cur_module = mod_name(current)
        other_modules = modules.copy()
        other_modules.remove(cur_module)

        # line containing 'import'
        import_lines = [line for line in open(current) if 'import' in line]

        for line in import_lines:
            # for each dependency
            for dep_module in [deps for deps in other_modules if deps in line]:
                associations.append((cur_module, dep_module))

    return associations


def extract_subpackage(path):
    """
    >>> extract_subpackage('gateway_code/control_node/cn.py')
    'control_node'

    >>> extract_subpackage('gateway_code/utils/serial_expect.py')
    'utils'

    >>> extract_subpackage('gateway_code/common.py')

    """
    parts = path.split('/')
    if len(parts) == 2:
        return None
    else:
        assert len(parts) == 3
        return parts[1]


def extract_clusters(files):

    clusters = {}
    for current in files:
        cur_module = mod_name(current)
        subpackage = extract_subpackage(current)
        if subpackage is not None:
            clusters.setdefault(subpackage, []).append(cur_module)
    return clusters


def str_cluster(cluster, nodes):
    nodes_str = ''
    for node in nodes:
        nodes_str += 8 * ' ' + node + ';\n'

    return CLUSTER_FMT % (cluster, cluster, nodes_str)


def generate_dot(files):
    ret = ''
    ret += HEADER
    for associations in extract_associations(files):
        ret += NODE_LINK % associations
        if associations[1] in ('config', 'common'):
            ret += ' [style=invis, constraint=false]'
        ret += '\n'

    for cluster, nodes in extract_clusters(files).iteritems():
        ret += str_cluster(cluster, nodes)

    # clusters
    ret += FOOTER
    return ret


FILE = 'gateway_code'


def main():
    dot_path = '%s.dot' % FILE
    png_path = '%s.png' % FILE

    files = check_output('find gateway_code/ -name \*py'
                         ' ! -name __init__.py'
                         ' -not -path "*integration/*"'
                         ' -not -path "*cli/*"'
                         ' -not -path "*tests*"', shell=True).splitlines()

    dot = generate_dot(files)
    with open('%s.dot' % FILE, 'w+') as dot_file:
        dot_file.write(dot)
        logging.debug("Dot written to %r", dot_path)
    try:
        check_call(['dot', '-T', 'png', dot_path, '-o', png_path])
    except OSError as err:
        logging.error("Cand find 'dot'. Graphviz is not installed")
        logging.error("%s", err)
    else:
        logging.debug("PNG written to %r", dot_path)


if __name__ == '__main__':
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    main()
