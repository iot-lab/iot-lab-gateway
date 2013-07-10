#! /usr/bin/python -u
# -*- coding:utf-8 -*-


import sys
import os
import shlex
import time
import threading
from subprocess import Popen, PIPE


SOCAT_CMD = 'socat -d -d PTY,link=%s,raw,echo=0,b500000  -'


def get_str(char_list):
    return ''.join([chr(char) for char in char_list])


def make_pkt(char_list):
    payload = get_str(char_list)
    return chr(0x80) + chr(len(payload)) + payload


ANSWERS = {
    # consumption
    get_str([0x79, 0, 0]): [[0x79, 0xA]],
    # 3.3V pvc 1100 512
    get_str([0x79, 0x17, 0xe4]): [[0x79, 0xA], [0xFA, 0x79, 0x17]],
    # 3.3V  v  1100 512
    get_str([0x79, 0x12, 0xe4]): [[0x79, 0xA], [0xFA, 0x79, 0x12]],
    # start/stop DC
    get_str([0x70, 0]): [[0x70, 0xA]],
    get_str([0x70, 1]): [[0x70, 0xA]],
    get_str([0x71, 0]): [[0x71, 0xA]],
    get_str([0x71, 1]): [[0x71, 0xA]],
    # reset_time
    get_str([0x72]): [[0x72, 0xA], [0xFA, 0x72]],
}

MEASURES = {
    get_str([0x79]): {
        get_str([0x00, 0x00]): None,
        get_str([0x17, 0xe4]):
        [0xFF, 0x01, 0xF6, 0x10, 0x01, 0x00, 0x75, 0x82, 0x84, 0x3E,
         0x3D, 0x0A, 0x4F, 0x40, 0xCC, 0xD8, 0xA3, 0x3D],
        get_str([0x12, 0xe4]):
        [0xFF, 0x01, 0xE9, 0x91, 0x03, 0x00, 0x3D, 0x0A, 0x4F, 0x40],
    }
}


class MeasuresState(object):

    def __init__(self):
        self.measures_dict = {str(0x79): None}
        self.mutex = threading.Semaphore(1)
        self.pty = None

        _thread = threading.Thread(target=self.send_measures_thread)
        _thread.daemon = True  # thread dies with the program
        _thread.start()

    def update_measures(self, str_payload):
        meas_type = str_payload[0]
        try:
            self.measures_dict[meas_type] = MEASURES[meas_type][str_payload[1:]]
        except KeyError:
            # does not update measures
            pass

    def get_measures(self):
        return [measure for measure in self.measures_dict.itervalues()
                if measure is not None]

    def send_measures_thread(self):
        while True:
            time.sleep(1)
            if self.pty is None:
                continue

            with self.mutex:
                measures = MEASURES_STATE.get_measures()
                for measure in measures:
                    print 'measure: %r' % measure
                    self.pty.write(make_pkt(measure))
                    time.sleep(0.20)


MEASURES_STATE = MeasuresState()


def control_node_stub(pkt_str, pty_in):
    with MEASURES_STATE.mutex:
        answers_list = ANSWERS.get(pkt_str, [])
        for answer in answers_list:
            print 'ANSWER: %r' % answer
            pty_in.write(make_pkt(answer))
            time.sleep(0.20)

        MEASURES_STATE.update_measures(pkt_str)


def main(argv):
    pty_path = parse_args(argv)

    socat_args = shlex.split(SOCAT_CMD % pty_path)
    print socat_args
    socat_process = Popen(socat_args, stdin=PIPE, stdout=PIPE)
    MEASURES_STATE.pty = socat_process.stdin

    while True:
        rec_chars = socat_process.stdout.read(1)

        if rec_chars != chr(0x80):
            print 'DROPPING, not sync'
            continue
        print 'SYNC',
        length = ord(socat_process.stdout.read(1))
        print length, ':',
        payload = socat_process.stdout.read(length)

        for i in payload:
            print 'x%x' % ord(i),
        print ''
        control_node_stub(payload, socat_process.stdin)

    socat_process.terminate()


def parse_args(argv):

    try:
        pty_path = os.path.abspath(argv[1])
    except IndexError:
        print >> sys.stderr, 'USAGE: %s PTY_PATH' % argv[0]
        exit(1)

    return pty_path

if __name__ == '__main__':
    main(sys.argv)
