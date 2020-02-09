import time
from threading import Event
from py9b.link.base import LinkOpenException, LinkTimeoutException
from py9b.transport.base import BaseTransport as BT
from py9b.command.regio import ReadRegs, WriteRegs
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.clock import mainthread
from kivy.properties import BooleanProperty, StringProperty, ObjectProperty
from utils import tprint, specialthread
import asyncio
from threading import Event

class Client(EventDispatcher):
    state = StringProperty('disconnected')
    transport = StringProperty('')
    address = ObjectProperty('')
    link = StringProperty('')

    _link = None
    _tran = None

    def __init__(self):
        self.register_event_type('on_error')
        super(Client, self).__init__()
        self.loop = None
        self.stay_connected = False

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
                if platform == 'android':
                    from py9b.link.droidserial import SerialLink
                    link = SerialLink(timeout=1.0)
                else:
                    from py9b.link.serial import SerialLink
                    link = SerialLink(timeout=1.0)

            elif self.link == 'mock':
                from mocklink import MockLink
                link = MockLink()

            elif self.link == None:
                tprint('select interface first')
                self.disconnect()

            if self.transport is '':
                self.disconnect()
                tprint('select protocol first')

            if self.transport is not '' and self.link is not None:
                link.__enter__()
                # This is split into two parts due to some link implementations
                # (namely droidble) requiring some initalization in main thread...
                self._connect_inner(link)
            else:
                tprint('One or more parameters are not set')

        except Exception as exc:
            self.dispatch('on_error', repr(exc))
            raise exc

    @specialthread
    def _connect_inner(self, link):
        try:
            if self.address is '':
                ports = link.scan()
                if not link.scanned.is_set():
                    link.scanned.wait(link.timeout)
                if not ports:
                    raise Exception('No devices found')
                if isinstance(ports[0], tuple):
                    self.address = ports[0][1]
                else:
                    self.address = ports[0]
                link.open(self.address)
            elif self.address is not '':
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

            if not self._link.connected.is_set():
                self._link.connected.wait(self._link.timeout*1.5)

            if self._link.connected.is_set():
                self.update_state('connected')
            else:
                self.disconnect()

            return transport

        except Exception as exc:
            self.dispatch('on_error', repr(exc))
            raise exc

    @mainthread
    def update_state(self, state):
        print('Current state:', state)
        self.state = state

    def disconnect(self):
        self.update_state('disconnecting')
        self.address = ''
        try:
            self._link.close()
            self._link = None
            self._tran = None
        except:
            pass
        self.update_state('disconnected')

    def on_error(self, *args):
        self.disconnect()
        if self.stay_connected:
            self.connect()
        # Required for event handling dispatch
        pass
