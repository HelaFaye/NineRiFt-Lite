from __future__ import print_function
from sys import exit
import os

from kivy.app import App

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput

from py9b.link.base import LinkOpenException, LinkTimeoutException
from py9b.transport.base import BaseTransport as BT
from py9b.transport.xiaomi import XiaomiTransport
from py9b.transport.ninebot import NinebotTransport
from py9b.command.regio import ReadRegs, WriteRegs
from py9b.command.update import *

PING_RETRIES = 20
device = ''
fwfilep = ''
interface = 'bleandroid'
protocol = 'ninebot'
address = ''
devices = {'ble': BT.BLE, 'esc': BT.ESC, 'bms': BT.BMS, 'extbms': BT.EXTBMS}
protocols = {'xiaomi': XiaomiTransport, 'ninebot': NinebotTransport}

def setaddr(a):
	global address
	address = a
	print(address+' selected as host')

def setdev(d):
	global device
	device = d
	print(device+' selected as device')

def setfwfilep(f):
	global fwfilep
	fwfilep = f
	print(fwfilep+' selected as fwfile')

def checksum(s, data):
	for c in data:
		s += ord(c)
	return (s & 0xFFFFFFFF)

def UpdateFirmware(link, tran, dev, fwfile):
	print('flashing '+fwfilep+' to '+ device)
	fwfile.seek(0, os.SEEK_END)
	fw_size = fwfile.tell()
	fwfile.seek(0)
	fw_page_size = 0x80

	dev = devices.get(device)
	print('Pinging...', end='')
	for retry in range(PING_RETRIES):
		print('.', end='')
		try:
			if dev==BT.BLE:
				tran.execute(ReadRegs(dev, 0, '13s'))
			else:
				tran.execute(ReadRegs(dev, 0x10, '14s'))
		except LinkTimeoutException:
			continue
		break
	else:
		print('Timed out !')
		return False
	print('OK')

	if interface!='tcpnl':
		print('Locking...')
		tran.execute(WriteRegs(BT.ESC, 0x70, '<H', 0x0001))
	else:
		print('Not Locking...')

	print('Starting...')
	tran.execute(StartUpdate(dev, fw_size))

	print('Writing...')
	page = 0
	chk = 0
	while fw_size:
		chunk_sz = min(fw_size, fw_page_size)
		data = fwfile.read(chunk_sz)
		chk = checksum(chk, data)
		#tran.execute(WriteUpdate(dev, page, data))
		tran.execute(WriteUpdate(dev, page, data+b'\x00'*(fw_page_size-chunk_sz))) # TODO: Ninebot wants this padding. Will it work on M365 too?
		page += 1
		fw_size -= chunk_sz

	print('Finalizing...')
	tran.execute(FinishUpdate(dev, chk ^ 0xFFFFFFFF))

	print('Reboot')
	tran.execute(RebootUpdate(dev))
	print('Done')
	return True

def Flash(self, fwfilepath):
	if device=='extbms' and protocol!='ninebot':
		exit('Only Ninebot supports External BMS !')
	setfwfilep(fwfilepath)
	file = open(fwfilep, 'rb')
	dev = devices.get(device)
	if interface=='bleandroid':
		try:
			from py9b.link.bleandroid import BLELink
		except:
			exit('BLE is not supported on your system !')
		link = BLELink()
	elif interface=='tcp':
		from py9b.link.tcp import TCPLink
		link = TCPLink()
	elif interface=='serial':
		from py9b.link.serial import SerialLink
		link = SerialLink()
	else:
		exit('!!! BUG !!! Unknown interface selected: '+interface)

	with link:
		tran = protocols.get(protocol)(link)

		if address!='':
			addr = address
		elif interface!='bleandroid':
		 	print('Scanning...')
		 	ports = link.scan()
		 	if not ports:
		 		exit("No interfaces found !")
		 	print('Connecting to', ports[0][0])
		 	addr = ports[0][1]
		else:
		 	raise LinkOpenException
			#commented out because of LinkOpenException despite address specified
		link.open(addr)
		print('Connected')
		try:
			UpdateFirmware(link, tran, dev, file)
		except Exception as e:
			print('Error:', e)
			raise




class NineRiFt(App):

	def build(self):
		root_folder = getattr(self, 'user_data_dir')
		cache_folder = os.path.join(root_folder, 'cache')

		title_label = Label(text="NineRiFt", font_size='12sp',
		 size_hint_x=1, height='16sp')

		seladdr_label = Label(text="Addr:", font_size='12sp', height='14sp',
		 size_hint_y=1, size_hint_x=.08)

		seladdr_input = TextInput(multiline=False, text=address,
		height='12sp', font_size='12sp', size_hint_x=.92, size_hint_y=1)

		seladdr_input.bind(on_text_validate=lambda x: setdev(seladdr_input.text))

		selfile_label = Label(text="FW file:", font_size='12sp', size_hint_x=1, height='12sp')

		ble_button = Button(text="BLE", font_size='12sp', height='15sp',
		 on_press=lambda x:setdev('ble'))

		esc_button = Button(text="ESC", font_size='12sp', height='15sp',
		 on_press=lambda x:setdev('esc'))

		bms_button = Button(text="BMS", font_size='12sp', height='15sp',
		 on_press=lambda x:setdev('bms'))

		ebms_button = Button(text="EBMS", font_size='12sp', height='15sp',
		 on_press=lambda x:setdev('extbms'))

		selfile = FileChooserListView(path=cache_folder)

		flash_button = Button(text="Flash", font_size='15sp', height='16sp',
		 on_press=lambda x:Flash(selfile.selection[0]))

		titlelayout = BoxLayout(orientation='vertical', size_hint_y=.15)
		titlelayout.add_widget(title_label)

		toplayout = GridLayout(rows=2, size_hint_y=.2)
		addrlayout = BoxLayout(orientation='horizontal', size_hint_y=.3)
		addrlayout.add_widget(seladdr_label)
		addrlayout.add_widget(seladdr_input)
		topbtnlayout = BoxLayout(orientation='horizontal', size_hint_y=.7)
		topbtnlayout.add_widget(ble_button)
		topbtnlayout.add_widget(esc_button)
		topbtnlayout.add_widget(bms_button)
		topbtnlayout.add_widget(ebms_button)
		toplayout.add_widget(addrlayout)
		toplayout.add_widget(topbtnlayout)

		midlayout = BoxLayout(orientation='vertical', size_hint_y=.85)
		midlabelbox = AnchorLayout(anchor_y='top', size_hint_y=.1)
		midlabelbox.add_widget(selfile_label)
		midlayout.add_widget(midlabelbox)
		midlayout.add_widget(selfile)

		botlayout = BoxLayout(orientation='vertical', size_hint_y=.2)
		botlayout.add_widget(flash_button)
		flash_button = Button(text="Flash", font_size='18sp', height='20sp')
		#botlayout.add_widget(pb)

		mainlayout = GridLayout(cols=1, rows=4)
		mainlayout.add_widget(titlelayout)
		mainlayout.add_widget(toplayout)
		mainlayout.add_widget(midlayout)
		mainlayout.add_widget(botlayout)
		return mainlayout

if __name__ == "__main__":
	NineRiFt().run()
