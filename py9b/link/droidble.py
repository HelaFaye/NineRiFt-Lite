"""BLE link using ABLE"""

from __future__ import absolute_import
try:
	from able import GATT_SUCCESS, Advertisement, BluetoothDispatcher
except ImportError:
	exit('error importing able')
try:
	from .base import BaseLink, LinkTimeoutException, LinkOpenException
except ImportError:
	exit('error importing .base')
from binascii import hexlify
from kivy.logger import Logger
from kivy.properties import ObjectProperty

try:
	import queue
except ImportError:
	import Queue as queue

SCAN_TIMEOUT = 3

class Fifo():
	def __init__(self):
		self.q = queue.Queue()

	def write(self, data): # put bytes
		for b in data:
			self.q.put(b)

	def read(self, size=1, timeout=None): # but read string
		res = ''
		for i in xrange(size):
			res += chr(self.q.get(True, timeout))
		return res

class BLELink(BaseLink, BluetoothDispatcher):
	def __init__(self, *args, **kwargs):
		super(BLELink, self).__init__(*args, **kwargs)
		self.rx_fifo = Fifo()
		self.tx_characteristic = ObjectProperty(None)
		self.rx_characteristic = ObjectProperty(None)
		self.addr = ObjectProperty(None)
		self.ble_device = ObjectProperty(None)

	def __enter__(self):
		return self


	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	identity = bytearray([
	0x4e, 0x42  # Ninebot Bluetooth ID
    ])

	service_ids = {
	'retail': '6e400001-b5a3-f393-e0a9-e50e24dcca9e' #service UUID
    }

	receive_ids = {
    'retail': '6e400002-b5a3-f393-e0a9-e50e24dcca9e' #receive characteristic UUID
    }

	transmit_ids = {
    'retail': '6e400003-b5a3-f393-e0a9-e50e24dcca9e' #transmit characteristic UUID
    }

	scoot_found = False

	def discover(self):
		self.start_scan()
		self.state = 'scan'


	def on_device(self, device, rssi, advertisement):
		global scoot_found
		scoot_found = False
		if self.state != 'scan':
			return
		Logger.debug("on_device event {}".format(list(advertisement)))
		address = device.getAddress()
		if self.addr and address.startswith(self.addr):  # is a Mi Band device
			self.ble_device = device
			scoot_found = True
			self.stop_scan()
		else:
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
			self.close_gatt()
			self.services = None

	def on_services(self, status, services):
		self.services = services
		for uuid in receive_ids.values():
			self.rx_characteristic = self.services.search(uuid)
		for uuid in transmit_ids.values():
			self.tx_characteristic = self.services.search(uuid)
			self.enable_notifications(self.tx_characteristic)

	def on_characteristic_changed(self, characteristic):
		if characteristic == self.tx_characteristic:
			data = characteristic.getValue()
			self.rx_fifo.write(data)

	def open(self, port):
		self.tx_characteristic = self.rx_characteristic = None
		self.addr = port
		discover()

	def close(self):
		self.close_gatt()
		self.services = None

	def read(self, size):
		try:
			data = self.rx_fifo.read(size, timeout=self.timeout)
		except queue.Empty:
			raise LinkTimeoutException
		if self.dump:
			print '<', hexlify(data).upper()
		return data

	def write(self, data):
		if self.dump:
			print '>', hexlify(data).upper()
		size = len(data)
		ofs = 0
		while size:
			chunk_sz = min(size, _write_chunk_size)
			self.write_characteristic(rx_characteristic, bytearray(data[ofs:ofs+chunk_sz]))
			ofs += chunk_sz
			size -= chunk_sz

	def scan(self):
		discover()

__all__ = ['BLELink']
