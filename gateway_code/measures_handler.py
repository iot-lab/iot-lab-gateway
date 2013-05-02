# -*- coding:utf-8 -*-

"""
Control node measures reader
"""
from datetime import datetime
import Queue
from gateway_code import protocol
import threading

class MeasuresReader(object):

    def __init__(self, measures_queue, handler=None):
        self.measures_queue = measures_queue
        self.handler = handler
        self.reader_thread = None


    def start(self, handler_arg=None):
        if self.reader_thread is not None:
            return 1
        self.reader_thread = MeasuresReaderThread(self.measures_queue, \
                self.handler, handler_arg)
        self.reader_thread.start()
        return 0


    def stop(self):
        if self.reader_thread is None:
            return 1
        self.reader_thread.stop()
        self.reader_thread = None
        return 0


class MeasuresReaderThread(threading.Thread):

    def __init__(self, measures_queue, handler=None, handler_arg=None):

        super(MeasuresReaderThread, self).__init__()

        self.queue       = measures_queue
        self.handler     = handler
        self.stopped     = False
        self.handler_arg = handler_arg

        self.ref_time    = datetime.now()


    def update_time(self, new_time):
        # TODO, update time when apropriate packet is received
        self.ref_time = new_time


    def stop(self):
        self.stopped = True


    def run(self):

        self.stopped = False

        while not self.stopped:
            try:
                raw_pkt = self.queue.get(True, timeout=1)
                measure_pkt = protocol.decode_measure_packet(raw_pkt, \
                        self.ref_time)
                if self.handler is not None:
                    self.handler(measure_pkt, self.handler_arg)
            except Queue.Empty:
                pass

        return 0





