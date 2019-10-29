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

from threading import Event

try:
    from kivymd.toast import toast
except:
    print('no toast for you')


identity = bytearray(
    [
        0x4E, 0x42, 0x21, 0x00, 0x00, 0x00, 0x00, 0xDE,  # Ninebot Bluetooth ID 4E422100000000DE
        0x4E, 0x42, 0x21, 0x00, 0x00, 0x00, 0x00, 0xDF,  # Xiaomi M365 Bluetooth ID 4E422100000000DF
        0x4E, 0x42, 0x22, 0x01, 0x00, 0x00, 0x00, 0xDC,  # Xiaomi M365 Pro Bluetooth ID 4E422201000000DC
    ]
)

service_ids = {"retail": "6e400001-b5a3-f393-e0a9-e50e24dcca9e"}  # service UUID

receive_ids = {
    "retail": "6e400002-b5a3-f393-e0a9-e50e24dcca9e"# receive characteristic UUID
}

transmit_ids = {
    "retail": "6e400003-b5a3-f393-e0a9-e50e24dcca9e"# transmit characteristic UUID
}


SCAN_TIMEOUT = 5
_write_chunk_size = 20

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


class BLE(BluetoothDispatcher):
    def __init__(self):
        super(BLE, self).__init__()
        self.rx_fifo = Fifo()
        self.addr = ''
        self.ble_device = None
        self.scoot_found = False
        self.state = StringProperty()
        self.tx_characteristic = None
        self.rx_characteristic = None
        self.timeout = SCAN_TIMEOUT
        self.dump = True
        self.connected = Event()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def discover(self, timeout):
        self.start_scan()
        self.state = "scan"
        try:
            toast(self.state)
        except:
            print(self.state)
        self.connected.wait(timeout)
        self.stop_scan()


    def on_device(self, device, rssi, advertisement):
        if self.state != "scan":
            return
        Logger.debug("on_device event {}".format(list(advertisement)))
        address = device.getAddress()
        if self.addr and address.startswith(self.addr):
            print(address)
            self.ble_device = device
            self.scoot_found = True
            self.stop_scan()
        else:
            for ad in advertisement:
                print(ad)
                if ad.ad_type == Advertisement.ad_types.manufacturer_specific_data:
                    if ad.data.startswith(identity):
                        self.scoot_found = True
                    else:
                        break
                elif ad.ad_type == Advertisement.ad_types.complete_local_name:
                    name = str(ad.data)
        if self.scoot_found:
            self.state = "found"
            try:
                toast(self.state)
            except:
                print(self.state)
            self.ble_device = device
            Logger.debug("Scooter detected: {}".format(name))
            self.stop_scan()

    def on_scan_completed(self):
        if self.ble_device and self.state != "connected":
            self.connect_gatt(self.ble_device)
        else:
            self.close()

    def on_connection_state_change(self, status, state):
        if self.ble_device and self.state != "connected":
            self.discover_services()
        else:
            self.close()

    def on_services(self, status, services):
        self.services = services
        for uuid in receive_ids.values():
            self.rx_characteristic = self.services.search(uuid)
            print("RX: " + uuid)
        for uuid in transmit_ids.values():
            self.tx_characteristic = self.services.search(uuid)
            print("TX: " + uuid)
            self.enable_notifications(self.tx_characteristic, enable=True)
        if self.tx_characteristic and self.rx_characteristic:
            self.connected.set()
            self.state = "connected"
            try:
                toast(self.state)
            except:
                print(self.state)
        else:
            return

    def on_characteristic_changed(self, tx_characteristic):
        if self.tx_characteristic:
            data = self.tx_characteristic.getValue()
            self.rx_fifo.write(data)
            return

    def open(self, port):
        self.addr = port
        if not self.ble_device:
            self.scan()
        if self.ble_device and self.state != "connected":
            self.connect_gatt(self.ble_device)

    def close(self):
        if self.ble_device and self.state == 'connected':
            self.close_gatt()
        self.services = None
        self.rx_characteristic = None
        self.tx_characteristic = None
        self.connected.clear()
        self.state = "close"
        try:
            toast(self.state)
        except:
            print(self.state)

    def read(self, size):
        if self.ble_device and self.state == 'connected':
            try:
                data = self.rx_fifo.read(size, timeout=self.timeout)
            except queue.Empty:
                raise LinkTimeoutException
            if self.dump:
                print("<", hexlify(data).upper())
            return data

    def write(self, data):
        if self.ble_device and self.state == 'connected':
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

    def scan(self):
        self.discover(SCAN_TIMEOUT)


class BLELink(BaseLink):
    def __init__(self, *args, **kwargs):
        super(BLELink, self).__init__(*args, **kwargs)
        self._adapter = None

    def __enter__(self):
        self._adapter = BLE()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._adapter:
            self.close()

    def scan(self, timeout=SCAN_TIMEOUT):
        self._adapter.scan()

    def open(self, port):
        self._adapter.open(port)

    def close(self):
        self._adapter.close()

    def read(self, size):
        return self._adapter.read(size)

    def write(self, data):
        self._adapter.write(bytearray(data))


__all__ = ["BLELink"]
