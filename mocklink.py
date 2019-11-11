from struct import pack
import binascii

from py9b.link.base import BaseLink, LinkTimeoutException
from py9b.transport.base import checksum, BaseTransport as BT

try:
    import queue
except ImportError:
    import Queue as queue


class Fifo:
    def __init__(self):
        self.q = queue.Queue()

    def write(self, data):  # put bytes
        for b in data:
            self.q.put(b)

    def read(self, size=1, timeout=None):  # but read string
        res = bytearray()
        for i in range(size):
            res.append(self.q.get(True, timeout))
        return res


class MockLink:
    def __init__(self):
        self.q = Fifo()
        self.timeout = 1.0

    def __enter__(self):
        return self

    def scan(self):
        return [
            ('test', 'Test Device'),
        ]

    def close(self):
        print('Closed')

    def open(self, addr):
        print('Connected to', addr)

    def write(self, data):
        hdata = binascii.hexlify(data)
        print('>>', hdata.decode())
        if hdata == b'55aa032001680271ff':
            self.q.write(self._buildx(0x23, 0x01, 0x68, bytearray([0x01, 0x01])))

    def read(self, size=1):
        try:
            data = self.q.read(size, timeout=self.timeout)
        except queue.Empty:
            raise LinkTimeoutException
        return data

    def _buildx(self, dev, cmd, arg, data):
        pkt = (
            pack(
                "<BBBB",
                len(data) + 2,
                dev,
                cmd,
                arg,
            )
            + data
        )
        return b"\x55\xAA" + pkt + pack("<H", checksum(pkt))
