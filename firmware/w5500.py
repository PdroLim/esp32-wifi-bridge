# Minimal W5500 SPI Ethernet driver for MicroPython ESP32-S3
import time

# Common registers
_MR   = const(0x0000)
_GAR  = const(0x0001)
_SUBR = const(0x0005)
_SHAR = const(0x0009)
_SIPR = const(0x000F)
_PHYCFGR = const(0x002E)
_VERSIONR = const(0x0039)

# Socket register offsets
_Sn_MR    = const(0x0000)
_Sn_CR    = const(0x0001)
_Sn_SR    = const(0x0003)
_Sn_PORT  = const(0x0004)
_Sn_DIPR  = const(0x000C)
_Sn_DPORT = const(0x0010)
_Sn_TXBUF = const(0x001F)
_Sn_RXBUF = const(0x001E)
_Sn_TX_FSR= const(0x0020)
_Sn_TX_WR = const(0x0024)
_Sn_RX_RSR= const(0x0026)
_Sn_RX_RD = const(0x0028)

# Socket commands
_OPEN    = const(0x01)
_LISTEN  = const(0x02)
_CONNECT = const(0x04)
_CLOSE   = const(0x10)
_SEND    = const(0x20)
_RECV    = const(0x40)

# Socket status
_SOCK_CLOSED = const(0x00)
_SOCK_INIT   = const(0x13)
_SOCK_LISTEN = const(0x14)
_SOCK_ESTAB  = const(0x17)
_SOCK_CWAIT  = const(0x1C)

_TCP = const(0x21)


class W5500:
    def __init__(self, spi, cs, rst=None, mac=None):
        self._s = spi
        self._cs = cs
        self._cs.value(1)
        if rst:
            rst.value(0); time.sleep_ms(100)
            rst.value(1); time.sleep_ms(500)
        # Software reset
        self._w(0x0000, 0, b'\x80'); time.sleep_ms(100)
        # Verify chip
        v = self._r(0x0039, 0, 1)
        print(f"W5500 version: 0x{v[0]:02X} {'OK' if v[0]==4 else 'WARN'}")
        # MAC
        m = mac or b'\x00\x08\xDC\x01\x02\x03'
        self._w(0x0009, 0, m)
        # 2KB buffers per socket
        for n in range(8):
            self._w(0x001E, n*4+1, b'\x02')
            self._w(0x001F, n*4+1, b'\x02')

    def _ctrl(self, bsb, wr): return (bsb << 3) | (4 if wr else 0)

    def _w(self, addr, bsb, data):
        self._cs.value(0)
        self._s.write(bytes([addr >> 8, addr & 0xFF, self._ctrl(bsb, 1)]) + bytes(data))
        self._cs.value(1)

    def _r(self, addr, bsb, n):
        self._cs.value(0)
        self._s.write(bytes([addr >> 8, addr & 0xFF, self._ctrl(bsb, 0)]))
        d = self._s.read(n)
        self._cs.value(1)
        return d

    def ifconfig(self, ip, sub, gw):
        self._w(0x0001, 0, bytes(int(x) for x in gw.split('.')))
        self._w(0x0005, 0, bytes(int(x) for x in sub.split('.')))
        self._w(0x000F, 0, bytes(int(x) for x in ip.split('.')))

    def get_ip(self):
        return '.'.join(str(b) for b in self._r(0x000F, 0, 4))

    def link_up(self):
        return bool(self._r(0x002E, 0, 1)[0] & 1)

    def socket(self, n=0):
        return _Sock(self, n)


class _Sock:
    def __init__(self, nic, n):
        self._n = n
        self._w = nic
        self._timeout = 10.0

    def _rb(self): return self._n * 4 + 1
    def _tb(self): return self._n * 4 + 2
    def _xb(self): return self._n * 4 + 3

    def _cmd(self, c):
        self._w._w(0x0001, self._rb(), bytes([c]))
        t = 0
        while self._w._r(0x0001, self._rb(), 1)[0] and t < 200:
            time.sleep_ms(5); t += 1

    def _st(self): return self._w._r(0x0003, self._rb(), 1)[0]

    def settimeout(self, t): self._timeout = t

    def close(self):
        self._cmd(_CLOSE)

    def bind(self, port):
        self._w._w(0x0000, self._rb(), bytes([_TCP]))
        self._w._w(0x0004, self._rb(), bytes([port >> 8, port & 0xFF]))
        self._cmd(_OPEN)
        t = 0
        while self._st() != _SOCK_INIT and t < 50:
            time.sleep_ms(10); t += 1

    def listen(self):
        self._cmd(_LISTEN)

    def accept_ready(self):
        return self._st() == _SOCK_ESTAB

    def connect(self, ip, port):
        self._w._w(0x0000, self._rb(), bytes([_TCP]))
        self._w._w(0x000C, self._rb(), bytes(int(x) for x in ip.split('.')))
        self._w._w(0x0010, self._rb(), bytes([port >> 8, port & 0xFF]))
        self._cmd(_OPEN)
        self._cmd(_CONNECT)
        deadline = time.time() + self._timeout
        while self._st() != _SOCK_ESTAB:
            if self._st() == _SOCK_CLOSED or time.time() > deadline:
                raise OSError("connect failed")
            time.sleep_ms(50)

    def available(self):
        r = self._w._r(0x0026, self._rb(), 2)
        return (r[0] << 8) | r[1]

    def recv(self, size):
        n = self.available()
        if not n: return b''
        size = min(size, n)
        rd = self._w._r(0x0028, self._rb(), 2)
        ptr = (rd[0] << 8) | rd[1]
        data = self._w._r(ptr, self._xb(), size)
        ptr = (ptr + size) & 0xFFFF
        self._w._w(0x0028, self._rb(), bytes([ptr >> 8, ptr & 0xFF]))
        self._cmd(_RECV)
        return data

    def send(self, data):
        # wait for TX space
        for _ in range(200):
            fsr = self._w._r(0x0020, self._rb(), 2)
            if ((fsr[0] << 8) | fsr[1]) >= len(data): break
            time.sleep_ms(5)
        wr = self._w._r(0x0024, self._rb(), 2)
        ptr = (wr[0] << 8) | wr[1]
        self._w._w(ptr, self._tb(), data)
        ptr = (ptr + len(data)) & 0xFFFF
        self._w._w(0x0024, self._rb(), bytes([ptr >> 8, ptr & 0xFF]))
        self._cmd(_SEND)
        return len(data)

    def is_connected(self):
        st = self._st()
        return st in (_SOCK_ESTAB, _SOCK_CWAIT)