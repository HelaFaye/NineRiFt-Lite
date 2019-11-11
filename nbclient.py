import time
from threading import Event
from py9b.link.base import LinkOpenException, LinkTimeoutException
from py9b.transport.base import BaseTransport as BT
from py9b.command.regio import ReadRegs, WriteRegs
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.clock import mainthread
from kivy.properties import NumericProperty, BooleanProperty, StringProperty, ObjectProperty
from utils import tprint, sidethread
import asyncio

class Client(EventDispatcher):
    state = StringProperty('disconnected')
    transport = StringProperty('xiaomi')
    address = ObjectProperty('')
    link = StringProperty('ble')

    _link = None
    _tran = None

    def __init__(self):
        self.register_event_type('on_error')
        super(Client, self).__init__()
        self.loop = None

    @mainthread
    def connect(self):
        self.update_state('connecting')
        try:
            link = None
            if self.link == 'ble':
                if platform == 'android':
                    from py9b.link.droidble import BLELink
                    link = BLELink()
                else:
                    from py9b.link.bleak import BLELink
                    if self.loop is None:
                        self.loop = asyncio.get_event_loop()
                    link = BLELink(loop=self.loop)
            elif self.link == 'tcp':
                from py9b.link.tcp import TCPLink
                link = TCPLink()
            elif self.link == 'serial':
                from py9b.link.serial import SerialLink
                link = SerialLink(timeout=1.0)
            elif self.link == 'mock':
                from mocklink import MockLink
                link = MockLink()

            link.__enter__()

            # This is split into two parts due to some link implementations
            # (namely droidble) requiring some initalization in main thread...
            self._connect_inner(link)
        except Exception as exc:
            self.update_state('disconnected')
            self.dispatch('on_error', repr(exc))
            raise exc

    @sidethread
    def _connect_inner(self, link):
        try:
            if not self.address:
                if platform!='android':
                    ports = link.scan()
                    if not ports:
                        raise Exception('No devices found')
                    if isinstance(ports[0], tuple):
                        self.address = ports[0][1]
                    else:
                        self.address = ports[0]
                link.open(self.address)
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

            self._tran = transport
            self._link = link
            self.update_state('connected')

            return transport
        except Exception as exc:
            self.update_state('disconnected')
            self.dispatch('on_error', repr(exc))
            raise exc

    @mainthread
    def update_state(self, state):
        print('Current state:', state)
        self.state = state

    @sidethread
    def disconnect(self):
        if self.state == 'connected':
            self.update_state('disconnecting')
            self._link.close()
            self.update_state('disconnected')

    def on_error(self, *args):
        # Required for event handling dispatch
        pass
