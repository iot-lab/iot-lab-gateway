#! /usr/bin/python -u
# -*- coding:utf-8 -*-

import sys
import time


def main(command_file_path):
    """
    Delay-cat the file.
    Print all non empty lines and sleep 1 second after each line.

    Empty lines in the file are meant to be used as delay.
    """

    with open(command_file_path) as command_file:
        while True:
            line = command_file.readline()
            if len(line) == 0:
                break

            # non blank lines
            stripped_line = line.strip()
            if len(stripped_line) == 0:
                time.sleep(1)
                continue

            sys.stderr.write(stripped_line + '\n')
            # comments
            if stripped_line[0] == '#':
                continue

            print(stripped_line)
            # sleep after each line, blank lines act as delay
            time.sleep(1)


if __name__ == '__main__':
    sys.stderr.write(' '.join(sys.argv) + '\n')
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <command_file>\n" % sys.argv[0])
        exit(1)

    command_file_path = sys.argv[1]

    main(command_file_path)
