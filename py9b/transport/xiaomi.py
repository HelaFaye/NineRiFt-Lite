"""Xiaomi packet transport"""
from struct import pack, unpack
from .base import checksum, BaseTransport as BT
from .packet import BasePacket


class XiaomiTransport(BT):
    MASTER2ESC = 0x20
    ESC2MASTER = 0x23

    MASTER2BLE = 0x21
    BLE2MASTER = 0x24

    MASTER2BMS = 0x22
    BMS2MASTER = 0x25

    MOTOR = 0x01
    DEVFF = 0xFF

    _SaDa2Addr = {
        BT.HOST: {
            BT.MOTOR: MOTOR,
            BT.ESC: MASTER2ESC,
            BT.BLE: MASTER2BLE,
            BT.BMS: MASTER2BMS,
        },
        BT.ESC: {
            BT.HOST: ESC2MASTER,
            BT.BLE: MASTER2BLE,
            BT.BMS: MASTER2BMS,
            BT.MOTOR: MOTOR,
        },
        BT.BMS: {BT.HOST: BMS2MASTER, BT.ESC: BMS2MASTER, BT.MOTOR: MOTOR},
        BT.MOTOR: {BT.HOST: MOTOR, BT.ESC: MOTOR, BT.BMS: MOTOR},
    }

    # TBC
    _BleAddr2SaDa = {
        MASTER2ESC: (BT.HOST, BT.ESC),
        ESC2MASTER: (BT.ESC, BT.HOST),
        MASTER2BMS: (BT.HOST, BT.BMS),
        BMS2MASTER: (BT.BMS, BT.HOST),
        MASTER2BLE: (BT.HOST, BT.BLE),
        BLE2MASTER: (BT.BLE, BT.HOST),
        MOTOR: (BT.MOTOR, BT.HOST),
    }

    _BmsAddr2SaDa = {
        MASTER2ESC: (BT.BMS, BT.ESC),
        ESC2MASTER: (BT.ESC, BT.BMS),
        MASTER2BMS: (BT.ESC, BT.BMS),
        BMS2MASTER: (BT.BMS, BT.ESC),
        MASTER2BLE: (BT.BMS, BT.BLE),
        BLE2MASTER: (BT.BLE, BT.BMS),
        MOTOR: (BT.MOTOR, BT.BMS),
    }

    def __init__(self, link, device=BT.HOST):
        super(XiaomiTransport, self).__init__(link)
        self.device = device
        self.keys = None

    def _make_addr(self, src, dst):
        return XiaomiTransport._SaDa2Addr[src][dst]

    def _split_addr(self, addr):
        if self.device == BT.BMS:
            return XiaomiTransport._BmsAddr2SaDa[addr]
        else:
            return XiaomiTransport._BleAddr2SaDa[addr]

    def _wait_pre(self):
        while True:
            while True:
                c = self.link.read(1)
                if c == b"\x55":
                    break
            while True:
                c = self.link.read(1)
                if c == b"\xaa" or c == b"\xab":
                    return c
                if c != b"\x55":
                    break  # start waiting 55 again, else - this is 55, so wait for AA

    def recv(self):
        ver = self._wait_pre()
        pkt = self.link.read(1)
        l = ord(pkt) + 3 + (4 if ver == b"\xab" else 0)
        for i in range(l):
            pkt.extend(self.link.read(1))
        ck_calc = checksum(pkt[0:-2])
        ck_pkt = unpack("<H", pkt[-2:])[0]
        if ck_pkt != ck_calc:
            print("Checksum mismatch !")
            return None

        if ver == b"\xab":
            # Drops 2 bytes of garbage and 2 bytes of checksum, first 2 bytes
            # of garbage are dropped below
            pkt[1:] = self.encrypt(pkt[1:])[:-4]

        sa, da = self._split_addr(pkt[1])
        return BasePacket(sa, da, pkt[2], pkt[3], pkt[4:-2])  # sa, da, cmd, arg, data

    def send(self, packet):
        dev = self._make_addr(packet.src, packet.dst)
        if self.keys:
            pkt = pack("<B", len(packet.data) + 2)
            pkt += self.encrypt(
                pack("<BBB", dev, packet.cmd, packet.arg) + packet.data + (b"\x00" * 4)
            )
            pkt = b"\x55\xab" + pkt + pack("<H", checksum(pkt))
        else:
            pkt = (
                pack("<BBBB", len(packet.data) + 2, dev, packet.cmd, packet.arg)
                + packet.data
            )
            pkt = b"\x55\xaa" + pkt + pack("<H", checksum(pkt))
        self.link.write(pkt)

    def encrypt(self, data):
        k = self.keys
        return bytearray([b ^ (k[i] if i < len(k) else 0) for i, b in enumerate(data)])


__all__ = ["XiaomiTransport"]
