import time
from threading import Event
from py9b.link.base import LinkOpenException, LinkTimeoutException
from py9b.transport.base import BaseTransport as BT
from py9b.command.regio import ReadRegs, WriteRegs
from kivy.utils import platform
try:
    from kivymd.toast import toast
except:
    tprint('no toast for you')

# toast or print
def tprint(msg):
    try:
        toast(msg)
    except:
        print(msg)

class Client:
    def __init__(self):
        super(Client, self).__init__()
        self.transport = None
        self.link = None
        self.address = None
        self.connected = Event()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def setaddr(self, a):
        self.address = a
        tprint(self.address+' selected as address')

    def setiface(self, i):
        self.link = i.lower()
        tprint(self.link+' selected as interface')

    def setproto(self, p):
        self.transport = p.lower()
        tprint(self.transport+' selected as protocol')


    def connect(self):
        link = None
        if self.link == 'ble':
            if platform != 'android':
                from py9b.link.bleak import BLELink
            elif platform == 'android':
                from py9b.link.droidble import BLELink
            link = BLELink()
        elif self.link == 'tcp':
            from py9b.link.tcp import TCPLink
            link = TCPLink()
        elif self.link == 'serial':
            from py9b.link.serial import SerialLink
            link = SerialLink(timeout=1.0)

        link.__enter__()

        if not self.address:
            if platform!='android':
                ports = link.scan()
                if not ports:
                    raise Exception('No devices found')
                self.address = ports[0]
            elif platform=='android':
                link.open()
        elif self.address:
            link.open(self.address)

        transport = None
        if self.transport == 'ninebot':
            from py9b.transport.ninebot import NinebotTransport
            transport = NinebotTransport(link)
        elif self.transport == 'xiaomi':
            from py9b.transport.xiaomi import XiaomiTransport
            transport = XiaomiTransport(link)

            if transport.execute(ReadRegs(BT.ESC, 0x68, "<H"))[0] > 0x081 and self.link is ('ble'):
                transport.keys = link.fetch_keys()
                transport.recover_keys()
                tprint('Keys recovered')

        self._transport = transport
        self._link = link

        return transport
        self.connected.set()


    def disconnect(self):
        if self.connected.is_set():
            link.close()
            self.connected.clear()
            transport = None
            link = None
