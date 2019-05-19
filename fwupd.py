
from py9b.link.base import LinkOpenException, LinkTimeoutException
from py9b.transport.base import BaseTransport as BT
from py9b.transport.xiaomi import XiaomiTransport
from py9b.transport.ninebot import NinebotTransport
from py9b.command.regio import ReadRegs, WriteRegs
from py9b.command.update import *

class FWUpd(object):
    def __init__(self):
        self.devices = {'ble': BT.BLE, 'esc': BT.ESC, 'bms': BT.BMS, 'extbms': BT.EXTBMS}
        self.protocols = {'xiaomi': XiaomiTransport, 'ninebot': NinebotTransport}
        PING_RETRIES = 20
        self.device = 'esc'
        self.fwfilep = ''
        self.interface = 'tcp'
        self.protocol = 'ninebot'
        self.address = ''

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

    def checksum(s, data):
        for c in data:
            s += ord(c)
        return (s & 0xFFFFFFFF)

    def UpdateFirmware(self, link, tran, dev, fwfile):
        print('flashing '+fwfilep+' to ' + self.device)
        fwfile.seek(0, os.SEEK_END)
        fw_size = fwfile.tell()
        fwfile.seek(0)
        fw_page_size = 0x80

        dev = self.devices.get(self.device)
        print('Pinging...')
        for retry in range(PING_RETRIES):
            print('.')
            try:
                if dev == BT.BLE:
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

        if self.interface != 'tcpnl':
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
            tran.execute(WriteUpdate(dev, page, data+b'\x00'*(fw_page_size-chunk_sz)))
            page += 1
            fw_size -= chunk_sz

        print('Finalizing...')
        tran.execute(FinishUpdate(dev, chk ^ 0xFFFFFFFF))

        print('Reboot')
        tran.execute(RebootUpdate(dev))
        print('Done')
        return True

    def Flash(self, fwfilep):
        if self.device == 'extbms' and self.protocol != 'ninebot':
            exit('Only Ninebot supports External BMS !')
        self.setfwfilep(fwfilep)
        file = open(fwfilep, 'rb')
        dev = self.devices.get(self.device)
        if self.interface == 'ble':
            if platform != 'android':
                try:
                    from py9b.link.ble import BLELink
                except:
                    exit('BLE is not yet working with your configuration !')
            elif platform == 'android':
                try:
                    from py9b.link.bleandroid import BLELink
                except:
                    exit('BLE is not yet supported on Android !')
            else:
                exit('BLE is not supported on your system !')
            link = BLELink()
        elif self.interface == 'tcp':
            from py9b.link.tcp import TCPLink
            link = TCPLink()
        elif self.interface == 'serial':
            from py9b.link.serial import SerialLink
            link = SerialLink()
        else:
            exit('!!! BUG !!! Unknown interface selected: '+interface)

        with link:
            tran = self.protocols.get(self.protocol)(link)

            if self.address != '':
                addr = self.address
            elif self.interface != 'ble':
                print('Scanning...')
                ports = link.scan()
                if not ports:
                    exit("No interfaces found !")
                print('Connecting to', ports[0][0])
                addr = ports[0][1]
            else:
                raise LinkOpenException

            link.open(addr)
            print('Connected')
            try:
                UpdateFirmware(link, tran, dev, file)
            except Exception as e:
                print('Error:', e)
                raise
