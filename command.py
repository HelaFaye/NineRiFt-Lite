import time

from py9b.link.base import LinkTimeoutException
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



class Connection:
    def __init__(self, transport, link, address):
        self.transport = transport
        self.link = link
        self.address = address

    def __enter__(self):
        link = None
        if self.link == 'ble':
            if platform != 'android':
                from py9b.link.bleak import BLELink
            elif platform == 'android':
                from py9b.link.droidble import BLELink
        elif self.link == 'tcp':
            from py9b.link.tcp import TCPLink
            link = TCPLink()
        elif self.link == 'serial':
            from py9b.link.serial import SerialLink
            link = SerialLink(timeout=1.0)

        link.__enter__()

        if not self.address:
            ports = link.scan()
            if not ports:
                raise Exception('No devices found')
            self.address = ports[0]

        link.open(self.address)

        transport = None
        if self.transport == 'ninebot':
            from py9b.transport.ninebot import NinebotTransport
            transport = NinebotTransport(link)
        elif self.transport == 'xiaomi':
            from py9b.transport.xiaomi import XiaomiTransport
            transport = XiaomiTransport(link)

            if transport.execute(ReadRegs(BT.ESC, 0x68, "<H"))[0] > 0x081 and self.link.startswith('ble'):
                transport.keys = link.fetch_keys()
                transport.recover_keys()
                tprint('Keys recovered')

        self._transport = transport
        self._link = link

        return transport

    def __exit__(self, a, b, c):
        self._link.__exit__(a, b, c)


class Command:
    self.transport = ''
    self.link = ''
    self.address = ''
    self.new_sn = ''
    self.device = ''

    def connect(ctx, transport, link, address):
        ctx.obj = Connection(transport, link, address)

    def dump(ctx, device):
        dev = {
            'esc': BT.ESC,
            'ble': BT.BLE,
            'bms': BT.BMS,
            'extbms': BT.EXTBMS,
        }[device]
        with ctx.obj as tran:
            for offset in range(256):
                try:
                    tprint('0x%02x: %04x' % (offset, tran.execute(ReadRegs(dev, offset, "<H"))[0]))
                except Exception as exc:
                    tprint('0x%02x: %s' % (offset, exc))

    def sniff(ctx):
        with ctx.obj as tran:
            while True:
                try:
                    tprint(tran.recv())
                except LinkTimeoutException as exc:
                    pass
                except Exception as exc:
                    tprint(exc)

    def powerdown(ctx):
        with ctx.obj as tran:
            tran.execute(WriteRegs(BT.ESC, 0x79, "<H", 0x0001))
            tprint('Done')

    def lock(ctx):
        with ctx.obj as tran:
            tran.execute(WriteRegs(BT.ESC, 0x70, "<H", 0x0001))
            tprint('Done')

    def unlock(ctx):
        with ctx.obj as tran:
            tran.execute(WriteRegs(BT.ESC, 0x71, "<H", 0x0001))
            tprint('Done')

    def reboot(ctx):
        with ctx.obj as tran:
            tran.execute(WriteRegs(BT.ESC, 0x78, "<H", 0x0001))
            tprint('Done')

    def print_reg(tran, desc, reg, format, dev=BT.ESC):
        try:
            data = tran.execute(ReadRegs(dev, reg, format))
            tprint(desc % data)
        except Exception as exc:
            tprint(desc, repr(exc))

    def bms_info(tran, dev):
        tprint('BMS S/N:         %s' % tran.execute(ReadRegs(dev, 0x10, "14s"))[0].decode())
        print_reg(tran, 'BMS Version:     %04x', 0x17, "<H", dev=dev)
        print_reg(tran, 'BMS charge:      %d%%', 0x32, "<H", dev=dev)
        print_reg(tran, 'BMS full cycles: %d', 0x1b, "<H", dev=dev)
        print_reg(tran, 'BMS charges:     %d', 0x1c, "<H", dev=dev)
        print_reg(tran, 'BMS health:      %d%%', 0x3b, "<H", dev=dev)
        tprint('BMS current:     %.2fA' % (tran.execute(ReadRegs(dev, 0x33, "<h"))[0] / 100.0,))
        tprint('BMS voltage:     %.2fV' % (tran.execute(ReadRegs(dev, 0x34, "<h"))[0] / 100.0,))

    def info(ctx):
        with ctx.obj as tran:
            tprint('ESC S/N:       %s' % tran.execute(ReadRegs(BT.ESC, 0x10, "14s"))[0].decode())
            tprint('ESC PIN:       %s' % tran.execute(ReadRegs(BT.ESC, 0x17, "6s"))[0].decode())
            tprint('')
            print_reg(tran, 'BLE Version:   %04x', 0x68, "<H")
            print_reg(tran, 'ESC Version:   %04x', 0x1A, "<H")
            tprint('')
            print_reg(tran, 'Error code:    %d', 0x1B, "<H")
            print_reg(tran, 'Warning code:  %d', 0x1C, "<H")
            tprint('')
            tprint('Total mileage: %s' % pp_distance(tran.execute(ReadRegs(BT.ESC, 0x29, "<L"))[0]))
            tprint('Total runtime: %s' % pp_time(tran.execute(ReadRegs(BT.ESC, 0x32, "<L"))[0]))
            tprint('Total riding:  %s' % pp_time(tran.execute(ReadRegs(BT.ESC, 0x34, "<L"))[0]))
            tprint('Chassis temp:  %d°C' % (tran.execute(ReadRegs(BT.ESC, 0x3e, "<H"))[0] / 10.0,))
            tprint('')

            try:
                tprint(' *** Internal BMS ***')
                bms_info(tran, BT.BMS)
            except Exception as exc:
                tprint('No internal BMS found', repr(exc))

            tprint('')

            try:
                tprint(' *** External BMS ***')
                bms_info(tran, BT.EXTBMS)
            except Exception as exc:
                tprint('No external BMS found', repr(exc))

    def changesn(ctx, new_sn):
        from py9b.command.mfg import WriteSN, CalcSNAuth

        with ctx.obj as tran:
            old_sn = tran.execute(ReadRegs(BT.ESC, 0x10, "14s"))[0].decode()
            tprint("Old S/N:", old_sn)

            uid3 = tran.execute(ReadRegs(BT.ESC, 0xDE, "<L"))[0]
            tprint("UID3: %08X" % (uid3))

            auth = CalcSnAuth(old_sn, new_sn, uid3)
            # auth = 0
            tprint("Auth: %08X" % (auth))

            try:
                tran.execute(WriteSN(BT.ESC, new_sn.encode('utf-8'), auth))
                tprint("OK")
            except LinkTimeoutException:
                tprint("Timeout !")

            # save config and restart
            tran.execute(WriteRegs(BT.ESC, 0x78, "<H", 0x01))
            time.sleep(3)

            old_sn = tran.execute(ReadRegs(BT.ESC, 0x10, "14s"))[0]
            tprint("Current S/N:", old_sn)

    def pp_distance(dist):
        if dist < 1000:
            return '%dm' % dist
        return '%dkm %dm' % (dist / 1000.0, dist % 1000)

    def pp_time(seconds):
        periods = [
            ('year',        60*60*24*365),
            ('month',       60*60*24*30),
            ('day',         60*60*24),
            ('hour',        60*60),
            ('minute',      60),
            ('second',      1)
        ]

        strings = []
        for period_name, period_seconds in periods:
            if seconds > period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                has_s = 's' if period_value > 1 else ''
                strings.append("%2s %s%s" % (period_value, period_name, has_s))

        return " ".join(strings)
