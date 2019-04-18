"""BLE link using Android Bluetooth Low Energy Python library"""

from __future__ import absolute_import
from .base import BaseLink, LinkTimeoutException, LinkOpenException
from binascii import hexlify
from able import BluetoothDispatcher, GATT_SUCCESS, STATE_DISCONNECTED
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

class BLE(BluetoothDispatcher):
	device = client_characteristic = receive_characteristic = transmit_characteristic = None

	def start_client(self, addr, *args, **kwargs):
		self.rx_fifo = Fifo()
		self._addr = addr
		if self.device:  # device is already founded during the scan
			self.connect_gatt(self.device)  # reconnect
		else:
			self.stop_scan()  # stop previous scan
			self.start_scan()  # start a scan for devices

	def on_device(self, device, rssi, advertisement):
        # some device is found during the scan
		devices = self._adapter.scan(timeout=SCAN_TIMEOUT)
		for dev in devices:
			if dev['address'].startswith((self._addr)):  #finds scooters
				self.device = dev #picks the scoot
				self.stop_scan()

	def on_scan_completed(self):
		if self.device:
			self.connect_gatt(self.device)  # connect to device

	def on_connection_state_change(self, status, state):
		if status == GATT_SUCCESS and state:  # connection established
			self.discover_services()  # discover what services a device offer
		else:  # disconnection or error
			self.client_characteristic = None
			self.transmit_characteristic = None
			self.receive_characteristic = None
			self.close_gatt()  # close current connection

	def on_services(self, status, services):
		print(services)
		self.client_characteristic = services.search('2902')
		self.transmit_characteristic = services.search('6e400003-b5a3-f393-e0a9-e50e24dcca9e')
		self.receive_characteristic = services.search('6e400002-b5a3-f393-e0a9-e50e24dcca9e')
		self._adapter.enable_notifications(self.transmit_characteristic
		, enable=True)

	def write(self, barray):
		self.write_characteristic(self.receive_characteristic, barray)

	def on_characteristic_changed(self, transmit_characteristic):
		txchar = self.read_characteristic(self.transmit_characteristic)
		self.rx_fifo.write(txchar)

_write_chunk_size = 20 # as in android dumps

class BLELink(BaseLink):
	def __init__(self, *args, **kwargs):
		super(BLELink, self).__init__(*args, **kwargs)

	def __enter__(self):
		self._adapter = BLE()#defines api for use in BLE
		return self


	def __exit__(self, exc_type, exc_value, traceback):
		self.close()


	def scan(self, addr):
		pass


	def open(self, port):
		self._addr = port
		try:
			self._dev = self._adapter.start_client(self._addr)#performs connection using Address Type random
		except STATE_DISCONNECTED:
			raise LinkOpenException


	def close(self):
		if self._adapter:
			self._adapter.close_gatt()


	def read(self, size):
		try:
			data = self._adapter.rx_fifo.read(size, timeout=self.timeout)
		except data.Empty:
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
			self._adapter.write(bytearray(data[ofs:ofs+chunk_sz]))#writes byte array to characteristic
			ofs += chunk_sz
			size -= chunk_sz


__all__ = ['BLELink']
