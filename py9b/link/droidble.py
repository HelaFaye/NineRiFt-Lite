"""BLE link using ABLE"""

from __future__ import absolute_import

try:
    from able import GATT_SUCCESS, Advertisement, BluetoothDispatcher
except ImportError:
    exit("error importing able")
try:
    from .base import BaseLink, LinkTimeoutException, LinkOpenException
except ImportError:
    exit("error importing .base")
from binascii import hexlify
from kivy.logger import Logger
from kivy.properties import StringProperty

try:
    import queue
except ImportError:
    import Queue as queue

SCAN_TIMEOUT = 3

_write_chunk_size = 20

identity = bytearray(
    [
        0x4E,
        0x42,
        0x21,
        0x00,
        0x00,
        0x00,
        0x00,
        0xDE,  # Ninebot Bluetooth ID 4E422100000000DE
        0x4E,
        0x42,
        0x21,
        0x00,
        0x00,
        0x00,
        0x00,
        0xDF,  # Xiaomi Bluetooth ID 4E422100000000DF
    ]
)

service_ids = {"retail": "6e400001-b5a3-f393-e0a9-e50e24dcca9e"}  # service UUID

receive_ids = {
    "retail": "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # receive characteristic UUID
}

transmit_ids = {
    "retail": "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # transmit characteristic UUID
}

scoot_found = False


class Fifo:
    def __init__(self):
        self.q = queue.Queue()

    def write(self, data):  # put bytes
        for b in data:
            self.q.put(b)

    def read(self, size=1, timeout=None):  # but read string
        res = ""
        for i in xrange(size):
            res += chr(self.q.get(True, timeout))
        return res


class ScootBT(BluetoothDispatcher):
    def __init__(self):
        super(ScootBT, self).__init__()
        self.rx_fifo = Fifo()
        self.ble_device = None
        self.state = StringProperty()
        self.dump = True
        self.tx_characteristic = None
        self.rx_characteristic = None
        self.timeout = SCAN_TIMEOUT
        self.set_queue_timeout(self.timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def discover(self):
        self.start_scan()
        self.state = "scan"
        print(self.state)

    def on_device(self, device, rssi, advertisement):
        global scoot_found
        if self.state != "scan":
            return
        Logger.debug("on_device event {}".format(list(advertisement)))
        self.addr = device.getAddress()
        if self.addr and address.startswith(self.addr):
            print(self.addr)
            self.ble_device = device
            self.scoot_found = True
            self.stop_scan()
        else:
            for ad in advertisement:
                print(ad)
                if ad.ad_type == Advertisement.ad_types.manufacturer_specific_data:
                    if ad.data.startswith(self.identity):
                        scoot_found = True
                    else:
                        break
                elif ad.ad_type == Advertisement.ad_types.complete_local_name:
                    name = str(ad.data)
        if scoot_found:
            self.state = "found"
            print(self.state)
            self.ble_device = device
            Logger.debug("Scooter detected: {}".format(name))
            self.stop_scan()

    def on_scan_completed(self):
        if self.ble_device:
            self.connect_gatt(self.ble_device)
            self.state = "connected"
            print(self.state)
        else:
            self.start_scan()

    def on_connection_state_change(self, status, state):
        if status == GATT_SUCCESS and state:
            self.discover_services()
            self.state = "discover"
            print(self.state)
        else:
            self.close_gatt()
            self.rx_characteristic = None
            self.tx_characteristic = None
            self.services = None

    def on_services(self, status, services):
        self.services = services
        for uuid in receive_ids.values():
            self.rx_characteristic = self.services.search(uuid)
            print("RX: " + uuid)
        for uuid in transmit_ids.values():
            self.tx_characteristic = self.services.search(uuid)
            print("TX: " + uuid)
            self.enable_notifications(self.tx_characteristic)

    def on_characteristic_changed(self, characteristic):
        if characteristic == self.tx_characteristic:
            data = characteristic.getValue()
            self.rx_fifo.write(data)

    def open(self, port):
        self.addr = port
        if self.ble_device == None:
            self.discover()
        if self.state != "connected":
            self.connect_gatt(self.ble_device)
        else:
            return

    def close(self):
        if self.ble_device != None:
            self.close_gatt()
        self.services = None
        print("close")

    def read(self, size):
        print("read")
        if self.ble_device:
            try:
                data = self.rx_fifo.read(size, timeout=self.timeout)
            except queue.Empty:
                raise LinkTimeoutException
            if self.dump:
                print("<", hexlify(data).upper())
            return data
        else:
            print("BLE not connected")
            self.discover()

    def write(self, data):
        print("write")
        if self.ble_device:
            if self.dump:
                print(">", hexlify(data).upper())
            size = len(data)
            ofs = 0
            while size:
                chunk_sz = min(size, _write_chunk_size)
                self.write_characteristic(
                    self.rx_characteristic, bytearray(data[ofs : ofs + chunk_sz])
                )
                ofs += chunk_sz
                size -= chunk_sz
        else:
            print("BLE not connected")
            self.discover()

    def scan(self):
        self.discover()


class BLELink(BaseLink):
    def __init__(self, *args, **kwargs):
        super(BLELink, self).__init__(*args, **kwargs)
        self._adapter = None

    def __enter__(self):
        self._adapter = ScootBT()
        self._adapter.discover()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def scan(self):
        devices = self._adapter.scan()

    def open(self, port):
        self._adapter.open(port)

    def close(self):
        self._adapter.close()

    def read(self, size):
        self._adapter.read(size)

    def write(self, data):
        self._adapter.write(data)


__all__ = ["BLELink"]
