"""BLE link using Android Bluetooth Low Energy Python library"""

from __future__ import absolute_import
from .base import BaseLink, LinkTimeoutException, LinkOpenException
from binascii import hexlify
from able import GATT_SUCCESS, Advertisement, BluetoothDispatcher, STATE_DISCONNECTED
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

class NineBLE(BluetoothDispatcher):
	device = client_characteristic = receive_characteristic = transmit_characteristic = None
	address = ''

	def setaddr(self, a):
		global address
		address = a

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
            Logger.debug("Ninebot detected: {}".format(name))
            self.stop_scan()

	def write(self, barray):
		self.write_characteristic(self.receive_characteristic, barray) #writes packets to receive characteristic

	def on_characteristic_changed(self, transmit_characteristic):
		txchar = self.read_characteristic(self.transmit_characteristic) #reads packets from transmit characteristic
		self.rx_fifo.write(txchar) #into fifo

_write_chunk_size = 20

class BLELink(BaseLink):
	def __init__(self, *args, **kwargs):
		super(BLELink, self).__init__(*args, **kwargs)

	def __enter__(self):
		self._adapter = BLE() #defines class above for use in BLE
		return self


	def __exit__(self, exc_type, exc_value, traceback):
		self.close()


	def scan(self, addr):
		self._adapter.setaddr(addr)
		try:
			self._dev = self._adapter.start_client(self._addr)#performs connection
		except STATE_DISCONNECTED:
			raise LinkOpenException


	def open(self, port):
		self._adapter.setaddr(port)
		try:
			self._dev = self._adapter.start_client(self._addr)#performs connection
		except STATE_DISCONNECTED:
			raise LinkOpenException


	def close(self):
		if self._adapter:
			self._adapter.close_gatt() #closes connection


	def read(self, size):
		try:
			data = self._adapter.rx_fifo.read(size, timeout=self.timeout) #reads from receive fifo
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
			self._adapter.write(bytearray(data[ofs:ofs+chunk_sz])) #writes byte array to characteristic
			ofs += chunk_sz
			size -= chunk_sz


__all__ = ['BLELink']
