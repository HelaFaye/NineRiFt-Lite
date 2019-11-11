
from py9b.link.base import LinkOpenException, LinkTimeoutException
from py9b.transport.base import BaseTransport as BT
from py9b.transport.xiaomi import XiaomiTransport
from py9b.transport.ninebot import NinebotTransport
from py9b.command.regio import ReadRegs, WriteRegs
from py9b.command.update import *
from kivy.utils import platform
import os

try:
    from kivymd.toast import toast
except:
    print('no toast for you')

from nbclient import Client

# toast or print
def tprint(msg):
    try:
        toast(msg)
    except:
        print(msg)



class FWUpd(object):
    def __init__(self):
        self.devices = {'ble': BT.BLE, 'drv': BT.ESC, 'bms': BT.BMS, 'extbms': BT.EXTBMS}
        self.protocols = {'xiaomi': XiaomiTransport, 'ninebot': NinebotTransport}
        self.PING_RETRIES = 5
        self.device = ''
        self.fwfilep = ''
        self.interface = ''
        self.protocol = ''
        self.address = ''
        self.progress = 0
        self.maxprogress = 100
        self.nolock = False

    def setaddr(self, a):
        self.address = a
        tprint(self.address+' selected as address')

    def setdev(self, d):
        self.device = d.lower()
        tprint(self.device+' selected as device')

    def setfwfilep(self, f):
        self.fwfilep = f
        tprint(self.fwfilep+' selected as fwfile')

    def setiface(self, i):
        self.interface = i.lower()
        tprint(self.interface+' selected as interface')

    def setproto(self, p):
        self.protocol = p.lower()
        tprint(self.protocol+' selected as protocol')

    def setnl(self, b):
        if b=='nolock':
            self.nolock = True
        else:
            self.nolock = False
        tprint('no-lock set to '+str(self.nolock))

    def getprog(self):
        return self.progress

    def getmaxprog(self):
        return self.maxprogress

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

        if self.nolock is False:
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
            self.maxprogress = fw_size//fw_page_size+1
            self.progress = page
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

    def Flash(self, fwfilep):
        if self.device == 'extbms' and self.protocol != 'ninebot':
            exit('Only Ninebot supports External BMS !')
        self.setfwfilep(fwfilep)
        file = open(fwfilep, 'rb')
        dev = self.devices.get(self.device)
        tran = Client.connect()
        try:
            self.UpdateFirmware(tran, dev, file)
        except Exception as e:
            tprint('Error:', e)
            raise
