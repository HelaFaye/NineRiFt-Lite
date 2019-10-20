"""BLE link using ABLE"""

from able import BluetoothDispatcher, Advertisement, GATT_SUCCESS
from .base import BaseLink, LinkTimeoutException, LinkOpenException
from binascii import hexlify
from kivy.logger import Logger
from kivy.properties import StringProperty

try:
	import queue
except ImportError:
	import Queue as queue

import threading

class Fifo():
	def __init__(self):
		self.q = queue.Queue()

	def write(self, data): # put bytes
		for b in data:
			self.q.put(b)

	def read(self, size=1, timeout=None):  # read bytes
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
		self.dump = True
		self.identity = bytearray([
		0x4e, 0x42, 0x21, 0x00, 0x00, 0x00, 0x00, 0xDE#,  # Ninebot Bluetooth ID 4E422100000000DE
		#0x4e, 0x42, 0x21, 0x00, 0x00, 0x00, 0x00, 0xDF   # Xiaomi Bluetooth ID 4E422100000000DF
		])
		self.service_ids = {
		'retail': '6e400001-b5a3-f393-e0a9-e50e24dcca9e' #service UUID
		}

		self.receive_ids = {
		'retail': '6e400002-b5a3-f393-e0a9-e50e24dcca9e' #receive characteristic UUID
		}

		self.transmit_ids = {
		'retail': '6e400003-b5a3-f393-e0a9-e50e24dcca9e' #transmit characteristic UUID
		}
		self.tx_characteristic = None
		self.rx_characteristic = None
		self._write_chunk_size = 20
		self.timeout = 5
		self.queue_timeout = self.timeout

	def __enter__(self):
		return self


	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def discover(self):
		self.start_scan()
		self.state = 'scan'
		print(self.state)


	def on_device(self, device, rssi, advertisement):
		if self.state != 'scan':
			return
		Logger.debug("on_device event {}".format(list(advertisement)))
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
						self.scoot_found = True
					else:
						break

			if self.scoot_found:
				name = str(ad.data)
				self.ble_device = device
				Logger.debug("Scooter detected: {}".format(name))
				self.stop_scan()


	def on_scan_completed(self):
		if self.ble_device:
			self.connect_gatt(self.ble_device)
			print(self.state)
		else:
			self.start_scan()


	def on_connection_state_change(self, status, state):
		if status == GATT_SUCCESS and state:
			self.discover_services()
		else:
			self.close_gatt()
			self.rx_characteristic = None
			self.tx_characteristic = None
			self.services = None


	def on_services(self, status, services):
		self.services = services
		try:
			for uuid in self.receive_ids.values():
				self.rx_characteristic = self.services.search(uuid)
				print('RX: '+uuid)
			for uuid in self.transmit_ids.values():
				self.tx_characteristic = self.services.search(uuid)
				print('TX: '+uuid)
				self.enable_notifications(self.tx_characteristic, enable=True)
		except:
			print('no matching services found')

	def on_characteristic_changed(self, tx_characteristic):
		if self.tx_characteristic:
			data = tx_characteristic.getValue()
			self.rx_fifo.write(data)


	def open(self, port):
		self.addr = port
		if self.ble_device==None:
			self.discover()
		elif self.ble_device:
			return
		else:
			raise LinkOpenException


	def close(self):
		if self.ble_device != None:
			print('gclose')
			self.close_gatt()
		self.services = None
		print('close')


	def read(self, size):
		print('read')
		if self.ble_device:
			try:
				data = self.rx_fifo.read(size, timeout=self.timeout)
			except queue.Empty:
				raise LinkTimeoutException
			if self.dump:
				print('<', hexlify(data).upper())
			return data
		else:
			print('BLE not connected')
			self.discover()


	def write(self, data):
		print('write')
		if self.ble_device:
			if self.dump:
				print('>', hexlify(data).upper())
			size = len(data)
			ofs = 0
			while size:
				chunk_sz = min(size, self._write_chunk_size)
				self.write_characteristic(self.rx_characteristic, bytearray(data[ofs:ofs+chunk_sz]))
				ofs += chunk_sz
				size -= chunk_sz
		else:
			print('BLE not connected')
			self.discover()


	def scan(self):
		self.discover()

class BLELink(BaseLink):
	def __init__(self, *args, **kwargs):
		super(BLELink, self).__init__(*args, **kwargs)
		self._adapter = None
		self._rx_fifo = Fifo()
		self._adapter = BLE()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def scan(self):
		scant = threading.Thread(target=self._adapter.scan())
		scant.start()

	def open(self, port):
		self._adapter.open(port)


	def close(self):
		if self._adapter:
			self._adapter.close()

	def read(self, size):
		self._adapter.read(size)

	def write(self, data):
		self._adapter.write(data)


__all__ = ['BLELink']
