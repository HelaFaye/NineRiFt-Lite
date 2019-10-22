import asyncio

from bleak import discover, BleakClient
from py9b.link.base import BaseLink, LinkTimeoutException
from threading import Thread

_rx_char_uuid = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
_tx_char_uuid = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
_keys_char_uuid = "00000014-0000-1000-8000-00805f9b34fb"

_manuf_id = 0x424e
_manuf_data_ninebot = [33, 0, 0, 0, 0, 222]
_manuf_data_xiaomi =  [33, 0, 0, 0, 0, 223]
_manuf_data_xiaomi_pro =  [34, 1, 0, 0, 0, 220]

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


def run_worker(loop):
    print("Starting event loop", loop)
    asyncio.set_event_loop(loop)
    loop.run_forever()


class BleakLink(BaseLink):
    def __init__(self, device="hci0", loop=None, *args, **kwargs):
        self.device = device
        self.timeout = 5
        self.loop = loop or asyncio.get_event_loop()
        self._rx_fifo = Fifo()
        self._client = None
        self._th = None

    def __enter__(self):
        self.start()
        return self

    def start(self):
        if self._th:
            return

        self._th = Thread(target=run_worker, args=(self.loop,))
        self._th.daemon = True
        self._th.start()

    def __exit__(self, exc_type, exc_value, traceback):
        if self._client:
            self.close()

    def close(self):
        asyncio.run_coroutine_threadsafe(self._client.disconnect(), self.loop).result(
            10
        )

    def scan(self, timeout=1):
        devices = asyncio.run_coroutine_threadsafe(
            discover(timeout=timeout, device=self.device), self.loop
        ).result(timeout*3)

        # We need to keep scanning going for connect() to properly work
        asyncio.run_coroutine_threadsafe(
            discover(timeout=timeout, device=self.device), self.loop
        )

        return [
            (dev.name, dev.address)
            for dev in devices
            if dev.metadata.get('manufacturer_data', {}).get(_manuf_id, [])
                in [_manuf_data_xiaomi, _manuf_data_xiaomi_pro, _manuf_data_ninebot]
        ]

    def open(self, port):
        fut = asyncio.run_coroutine_threadsafe(self._connect(port), self.loop)
        fut.result(10)

    async def _connect(self, port):
        self._client = BleakClient(port[1], device=self.device)
        await self._client.connect()
        print("connected")
        await self._client.start_notify(_tx_char_uuid, self._data_received)
        print("services:", list(await self._client.get_services()))

    def _data_received(self, sender, data):
        self._rx_fifo.write(data)

    def write(self, data):
        fut = asyncio.run_coroutine_threadsafe(
            self._client.write_gatt_char(_rx_char_uuid, bytearray(data), False),
            self.loop,
        )
        return fut.result(3)

    def read(self, size):
        try:
            data = self._rx_fifo.read(size, timeout=self.timeout)
        except queue.Empty:
            raise LinkTimeoutException
        return data

    def fetch_keys(self):
        return asyncio.run_coroutine_threadsafe(
            self._client.read_gatt_char(_keys_char_uuid), self.loop
        ).result(5)
