# -*- coding:utf-8 -*-

"""
Control node measures reader
"""
from datetime import datetime
import Queue
from gateway_code import protocol
import threading

class MeasuresReader(object):

    def __init__(self, measures_queue):
        self.measures_queue = measures_queue
        self.reader_thread = None


    def start(self, user, exp_id):
        if self.reader_thread is not None:
            return 1
        self.reader_thread = MeasuresReaderThread(self.measures_queue, \
                user, exp_id)
        self.reader_thread.start()
        return 0


    def stop(self):
        if self.reader_thread is None:
            return 1
        self.reader_thread.stop()
        self.reader_thread = None
        return 0


class MeasuresReaderThread(threading.Thread):

    def __init__(self, measures_queue, user, exp_id):

        super(MeasuresReaderThread, self).__init__()

        self.queue    = measures_queue
        self.out_file = open('/tmp/%s_%s_measures.log' % (user, exp_id), 'wa')
        self.stopped  = False

        self.ref_time = datetime.now()


    def update_time(self, new_time):
        # TODO, update time when apropriate packet is received
        self.ref_time = new_time


    def stop(self):
        self.stopped = True
        self.out_file.close()


    def run(self):

        self.stopped = False

        while not self.stopped:
            try:
                raw_pkt = self.queue.get(True, timeout=1)
                measure_pkt = protocol.decode_measure_packet(raw_pkt, \
                        self.ref_time)

                # temporary output
                self.out_file.write(str(measure_pkt) + '\n')
            except Queue.Empty:
                pass

        return 0





