#! /usr/bin/env python
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
            line = line.strip()

            # non blank lines
            if len(line) != 0:
                print line
                print >> sys.stderr, line
            # sleep after each line, blank lines act as delay
            time.sleep(1)


if __name__ == '__main__':
    print >> sys.stderr, ' '.join(sys.argv)
    if len(sys.argv) != 2:
        print >> sys.stderr, "Usage: %s <command_file>" % sys.argv[0]
        exit(1)

    command_file_path = sys.argv[1]

    main(command_file_path)

