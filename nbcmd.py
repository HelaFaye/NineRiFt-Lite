import time
from py9b.link.base import LinkTimeoutException
from py9b.transport.base import BaseTransport as BT
from py9b.command.regio import ReadRegs, WriteRegs

from kivy.utils import platform
try:
    from kivymd.toast import toast
except:
    print('no toast for you')

# toast or print
def tprint(msg):
    try:
        toast(msg)
    except:
        print(msg)


class Command:
    def __init__(self, conn):
        self.device = ''
        self.conn = conn

    def setdev(self, d):
        self.device = d.lower()
        tprint(self.device+' selected as device')

    def powerdown(self):
        tran = self.conn._tran
        tran.execute(WriteRegs(BT.ESC, 0x79, "<H", 0x0001))
        tprint('Done')

    def lock(self):
        tran = self.conn._tran
        tran.execute(WriteRegs(BT.ESC, 0x70, "<H", 0x0001))
        tprint('Done')

    def unlock(self):
        tran = self.conn._tran
        tran.execute(WriteRegs(BT.ESC, 0x71, "<H", 0x0001))
        tprint('Done')

    def reboot(self):
        tran = self.conn._tran
        tran.execute(WriteRegs(BT.ESC, 0x78, "<H", 0x0001))
        tprint('Done')
