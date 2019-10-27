
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

class FWUpd(object):
    def __init__(self):
        self.devices = {'ble': BT.BLE, 'esc': BT.ESC, 'bms': BT.BMS, 'extbms': BT.EXTBMS}
        self.protocols = {'xiaomi': XiaomiTransport, 'ninebot': NinebotTransport}
        self.PING_RETRIES = 5
        self.device = 'esc'
        self.fwfilep = ''
        self.interface = 'ble'
        self.protocol = 'ninebot'
        self.address = ''
        self.progress = 0
        self.maxprogress = 100
        self.nolock = False

    def setaddr(self, a):
        self.address = a
        print(self.address+' selected as address')

    def setdev(self, d):
        self.device = d.lower()
        print(self.device+' selected as device')

    def setfwfilep(self, f):
        self.fwfilep = f
        print(self.fwfilep+' selected as fwfile')

    def setiface(self, i):
        self.interface = i.lower()
        print(self.interface+' selected as interface')

    def setproto(self, p):
        self.protocol = p.lower()
        print(self.protocol+' selected as protocol')

    def setnl(self, b):
        self.nolock = b
        print('no-lock set to'+self.nolock)

    def getprog(self):
        return self.progress

    def getmaxprog(self):
        return self.maxprogress

    def checksum(self, s, data):
        for c in data:
            s += c
        return (s & 0xFFFFFFFF)

    def UpdateFirmware(self, link, tran, dev, fwfile):
        print('update started')

        print('flashing '+self.fwfilep+' to ' + self.device)
        fwfile.seek(0, os.SEEK_END)
        fw_size = fwfile.tell()
        fwfile.seek(0)
        fw_page_size = 0x80

        dev = self.devices.get(self.device)


        for retry in range(self.PING_RETRIES):
            try:
                toast('Pinging...')
            except:
                print('Pinging...', end='')
            print(".", end="")
            try:
                if dev == BT.BLE:
                    tran.execute(ReadRegs(dev, 0, "13s"))
                else:
                    tran.execute(ReadRegs(dev, 0x10, "14s"))
            except LinkTimeoutException:
                continue
            break
        else:
            try:
                toast('TIMED OUT!!!'
            except:
                print("Timed out !")
            return False
        print("OK")

        if self.nolock is False:
            try:
                toast('Locking...')
            except:
                print('Locking...')
            tran.execute(WriteRegs(BT.ESC, 0x70, '<H', 0x0001))
        else:
            try:
                toast('Not Locking...')
            except:
                print('Not Locking...')

        print('Starting...')
        tran.execute(StartUpdate(dev, fw_size))

        try:
            toast('Writing...')
        except:
            print('Writing...')

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

        try:
            toast('Finalizing...')
        except:
            print('Finalizing...')
        tran.execute(FinishUpdate(dev, chk ^ 0xFFFFFFFF))

        print('Reboot')
        tran.execute(RebootUpdate(dev))
        try:
            toast('Done')
        except:
            print('Done')
        print('update finished')
        return True

    def Flash(self, fwfilep):
        if self.device == 'extbms' and self.protocol != 'ninebot':
            exit('Only Ninebot supports External BMS !')
        self.setfwfilep(fwfilep)
        file = open(fwfilep, 'rb')
        dev = self.devices.get(self.device)
        if self.interface == 'ble':
            if platform != 'android':
                from py9b.link.bleak import BLELink
            elif platform == 'android':
                try:
                    from py9b.link.droidble import BLELink
                except:
                    exit('BLE on Android failed to import!')
            else:
                exit('BLE is not supported on your system !')
            link = BLELink()
        elif self.interface == 'tcp':
            from py9b.link.tcp import TCPLink
            link = TCPLink()
        elif self.interface == 'serial':
            if platform == 'android':
                exit('Serial is not yet supported on Android !')
            from py9b.link.serial import SerialLink
            link = SerialLink()
        else:
            exit('!!! BUG !!! Unknown interface selected: '+self.interface)

        with link:
            tran = self.protocols.get(self.protocol)(link)

            if self.address:
                addr = self.address
                print('link address assigned')
            else:
                try:
                    addr = self.address
                    ports = None
                    print('Scanning...')
                    if self.interface != 'ble':
                        ports = link.scan()
                    if self.interface == 'ble':
                        link.scan()
                    if not self.interface=='ble' and not ports:
                        exit("No ports found !")
                        print('Connecting to', ports[0][0])
                        addr = ports[0][1]
                except:
                    raise LinkOpenException
            try:
                if self.interface=='ble' and platform != 'android':
                    devs = link.scan()
                    print(devs)
                    link.open(devs[0])
                else:
                    link.open(addr)
            except:
                print('failed to open link')
                raise LinkOpenException
            print('Connected')
            try:
                self.UpdateFirmware(link, tran, dev, file)
            except Exception as e:
                print('Error:', e)
                raise
