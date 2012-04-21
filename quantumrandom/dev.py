# Copyright (c) 2012 Luke Macken <lmacken@redhat.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

""" A multi-threaded Quantum Random Generator character device in userspace """

import sys
import cuse
import time
import threading
import quantumrandom

from cuse import cuse_api as libcuse

MAX_BUFFER = 100
threads = []
buffer = []


class RandomDataFetcher(threading.Thread):
    """A thread that fills a buffer with binary data"""
    running = False

    def run(self):
        global buffer
        self.running = True
        try:
            while self.running:
                if len(buffer) > MAX_BUFFER:
                    log("[Thread %d] Buffer at capacity; thread sleeping" %
                        self.id)
                    time.sleep(self.id + 1)
                    continue
                buffer.append(quantumrandom.binary())
                log("New random data buffered")
        except Exception, e:
            import traceback
            traceback.print_exc()
        self.running = False
        log("Thread done!")


class QuantumRandomDevice(object):

    def read(self, req, size, off, file_info):
        log("read(%s, %s, %s, %s)" % (req, size, off, file_info))
        global buffer, threads
        if not threads:
            log("Creating %d threads" % NUM_THREADS)
            for t in range(NUM_THREADS):
                thread = RandomDataFetcher()
                thread.setDaemon(True)
                thread.start()
                threads.append(thread)
        data = ''
        while len(data) < size:
            try:
                log("buffer size: %d" % len(buffer))
                data += buffer.pop(0)
                break
            except IndexError:
                log("no data")
                time.sleep(0.1)
                continue
        if len(data) > size:
            buffer.append(data[size:])
            data = data[:size]
        libcuse.fuse_reply_buf(req, data, len(data))

    def release(self, req, file_info):
        global threads
        dead = []
        for thread in threads:
            thread.running = False
            dead.append(thread)
        for thread in dead:
            threads.remove(thread)
        libcuse.fuse_reply_err(req, 0)



def log(msg):
    print(msg)


def main():
    if '-h' in sys.argv:
        raise SystemExit('Usage: %s [-v]')
    if '-v' not in sys.argv:
        global log
        def noop(msg):
            pass
        log = noop
    else:
        sys.argv.remove('-v')

    operations = QuantumRandomDevice()
    cuse.init(operations, 'qrandom', sys.argv[2:])

    try:
        cuse.main(True)
    except Exception, err:
        log("CUSE main ended %s" % str(err))


if __name__ == '__main__':
    main()
