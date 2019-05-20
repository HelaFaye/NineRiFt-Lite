from __future__ import absolute_import
from able import GATT_SUCCESS, Advertisement, BluetoothDispatcher
from .base import BaseLink, LinkTimeoutException, LinkOpenException
from binascii import hexlify
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.properties import ObjectProperty
import Queue

SCAN_TIMEOUT = 3


class Fifo():
	def __init__(self):
		self.q = Queue.Queue()

	def write(self, data): # put bytes
		for b in data:
			self.q.put(b)

	def read(self, size=1, timeout=None): # but read string
		res = ''
		for i in xrange(size):
			res += chr(self.q.get(True, timeout))
		return res

class BLELink(BaseLink, BluetoothDispatcher):

    ble_device = ObjectProperty(None)

    identity = bytearray([
        0x4e, 042,  # Ninebot Bluetooth ID
    ])

    receive_ids = {
        'retail': '6e400003-b5a3-f393-e0a9-e50e24dcca9e' #transmit characteristic UUID
    }

    transmit_ids = {
        'retail': '6e400002-b5a3-f393-e0a9-e50e24dcca9e' #receive characteristic UUID
    }

    service_ids = {
        'retail': '6e400001-b5a3-f393-e0a9-e50e24dcca9e' #transmit characteristic UUID
    }

    def discover(self):
        self.start_scan()
        self.state = 'scan'

    def on_device(self, device, rssi, advertisement):
        if self.state != 'scan':
            return
        Logger.debug("on_device event {}".format(list(advertisement)))
        scoot_found = False
        name = ''
        for ad in advertisement:
            if ad.ad_type == Advertisement.ad_types.manufacturer_specific_data:
                if ad.data.startswith(self.identity):
                    scoot_found = True
                else:
                    break
            elif ad.ad_type == Advertisement.ad_types.complete_local_name:
                name = str(ad.data)
        if scoot_found:
            self.state = 'found'
            self.ble_device = device
            Logger.debug("Scooter detected: {}".format(name))
            self.stop_scan()

    def on_scan_completed(self):
        if self.ble_device:
            self.connect_gatt(self.ble_device)
        else:
            self.start_scan()

    def on_connection_state_change(self, status, state):
        if status == GATT_SUCCESS and state:
            self.discover_services()
        else:
            self.alert_characteristic = None
            self.close_gatt()
            self.services = None

    def on_services(self, status, services):
        self.services = services
        for uuid in receive_ids.values():
            tx_characteristic = self.services.search(uuid)
        for uuid in transmit_ids.values():
            rx_characteristic = self.services.search(uuid)
            self.enable_notifications(rx_characteristic)

    def on_characteristic_changed(self, characteristic):
        uuid = characteristic.getUuid().toString()
        data = characteristic.getValue()
        Logger.debug("Characteristic {} changed value: {}".format(
            uuid, str(data).encode('hex')))
