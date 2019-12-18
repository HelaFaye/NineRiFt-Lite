import os

from py9b.link.base import LinkOpenException, LinkTimeoutException
from py9b.transport.base import BaseTransport as BT
from py9b.transport.xiaomi import XiaomiTransport
from py9b.transport.ninebot import NinebotTransport
from py9b.command.regio import ReadRegs, WriteRegs
from py9b.command.update import *

from kivy.utils import platform
from kivy.clock import mainthread
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, StringProperty, ObjectProperty
from utils import tprint, specialthread


class FWUpd(EventDispatcher):
    device = StringProperty('')
    lock = BooleanProperty(True)

    def __init__(self, conn):
        self.devices = {'ble': BT.BLE, 'drv': BT.ESC, 'bms': BT.BMS, 'extbms': BT.EXTBMS}
        self.protocols = {'xiaomi': XiaomiTransport, 'ninebot': NinebotTransport}
        self.PING_RETRIES = 3
        self.nolock = False
        self.conn = conn

    def checksum(self, s, data):
        for c in data:
            s += c
        return (s & 0xFFFFFFFF)

    def UpdateFirmware(self, tran, dev, fwfile):
        tprint('update started')

        tprint('flashing '+self.fwfilep+' to ' + self.device)
        fwfile.seek(0, os.SEEK_END)
        fw_size = fwfile.tell()
        fwfile.seek(0)
        fw_page_size = 0x80

        dev = self.devices.get(self.device)


        for retry in range(self.PING_RETRIES):
            tprint('Pinging...')
            try:
                if dev == BT.BLE:
                    tran.execute(ReadRegs(dev, 0, "13s"))
                else:
                    tran.execute(ReadRegs(dev, 0x10, "14s"))
            except LinkTimeoutException:
                continue
            break
        else:
            tprint("Timed out!")
            return False
        tprint("OK")

        if self.lock:
            tprint('Locking...')
            tran.execute(WriteRegs(BT.ESC, 0x70, '<H', 0x0001))
        else:
            tprint('Not Locking...')

        tprint('Starting...')
        tran.execute(StartUpdate(dev, fw_size))

        tprint('Writing...')

        page = 0
        chk = 0
        while fw_size:
            self.update_progress(page, fw_size // fw_page_size + 1)
            chunk_sz = min(fw_size, fw_page_size)
            data = fwfile.read(chunk_sz)
            chk = self.checksum(chk, data)
            tran.execute(WriteUpdate(dev, page, data+b'\x00'*(fw_page_size-chunk_sz)))
            page += 1
            fw_size -= chunk_sz

        tprint('Finalizing...')
        tran.execute(FinishUpdate(dev, chk ^ 0xFFFFFFFF))

        tprint('Reboot')
        tran.execute(RebootUpdate(dev))
        tprint('Done')
        tprint('update finished')
        return True

    @specialthread
    def Flash(self, fwfilep):
        if self.device == 'extbms' and self.conn.transport != 'ninebot':
            tprint('Only Ninebot supports External BMS !')
            return
        self.fwfilep = fwfilep
        file = open(fwfilep, 'rb')
        dev = self.devices.get(self.device)
        tran = self.conn._tran
        try:
            self.UpdateFirmware(tran, dev, file)
        except Exception as e:
            tprint('Error: %r' % (e,))
            raise

    @mainthread
    def update_progress(self, progress, maxprogress):
        setprogbar(progress, maxprogress)
