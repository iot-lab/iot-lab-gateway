# -*- coding:utf-8 -*-

"""
Control node measures reader
"""

import Queue
import threading

class MeasuresReader(object):
    """
    Control node Measures manager
    """

    def __init__(self, measures_queue, decoder):
        self.measures_queue = measures_queue
        self.reader_thread = None
        self.decoder = decoder


    def start(self, user, exp_id):
        """
        Start measures thread handler and manager
        """
        if self.reader_thread is not None: # pragma: no cover
            return 1
        self.reader_thread = MeasuresReaderThread(self.measures_queue, \
                self.decoder, user, exp_id)
        self.reader_thread.start()
        return 0


    def stop(self):
        """
        Stop measures thread handler and manager
        """
        if self.reader_thread is None: # pragma: no cover
            return 1
        self.reader_thread.stop()
        self.reader_thread = None
        return 0


class MeasuresReaderThread(threading.Thread):
    """
    Handle messages received from control node
    """

    def __init__(self, measures_queue, decoder, user, exp_id):

        super(MeasuresReaderThread, self).__init__()

        self.queue    = measures_queue
        self.decoder = decoder

        self.out_file = open('/tmp/%s_%s_measures.log' % (user, exp_id), 'wa')
        self.stopped  = False


    def stop(self):
        """
        stop thread
        """
        self.stopped = True
        self.out_file.close()


    def run(self):
        """
        Poll on measures queues and handle values
        """

        self.stopped = False

        while not self.stopped:
            try:
                raw_pkt = self.queue.get(True, timeout=1)
                measure_pkt = self.decoder(raw_pkt)

                # temporary output
                self.out_file.write(str(measure_pkt) + '\n')
            except Queue.Empty:
                pass

        return 0





