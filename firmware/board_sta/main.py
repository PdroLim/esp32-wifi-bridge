import network
import uasyncio as asyncio
from machine import UART, Pin, SPI
import time
import sys
import config

# ── Interface física ──────────────────────────────────────────
class RS485:
    def __init__(self):
        self.uart = UART(config.UART_ID, baudrate=config.UART_BAUD,
                         tx=config.UART_TX, rx=config.UART_RX,
                         bits=config.UART_BITS, parity=config.UART_PARITY,
                         stop=config.UART_STOP)
        print(f"RS485 UART{config.UART_ID} TX={config.UART_TX} RX={config.UART_RX} {config.UART_BAUD}bps")

    def any(self):
        return self.uart.any()

    def read(self, n):
        return self.uart.read(n)

    def write(self, data):
        self.uart.write(data)


class EthernetW5500:
    def __init__(self):
        try:
            import wiznet5k
        except ImportError:
            print("ERRO: driver wiznet5k nao encontrado.")
            print("Execute: mpremote connect <port> mip install wiznet5k")
            sys.exit(1)

        spi = SPI(config.ETH_SPI_ID, baudrate=2_000_000,
                  sck=Pin(config.ETH_CLK),
                  mosi=Pin(config.ETH_MOSI),
                  miso=Pin(config.ETH_MISO))
        cs  = Pin(config.ETH_CS,  Pin.OUT)
        rst = Pin(config.ETH_RST, Pin.OUT)

        self.nic = wiznet5k.WIZNET5K(spi, cs, rst)
        self.nic.ifconfig((config.ETH_IP, config.ETH_MASK, config.ETH_GW, "8.8.8.8"))
        print(f"Ethernet W5500 IP={config.ETH_IP}")

        self._srv = self.nic.socket()
        self._srv.bind(("", config.ETH_PORT))
        self._srv.listen(1)
        self._srv.settimeout(0)
        self._conn = None
        print(f"Ethernet aguardando conexao na porta {config.ETH_PORT}")

    def _ensure_conn(self):
        if self._conn is None:
            try:
                self._conn, addr = self._srv.accept()
                self._conn.settimeout(0)
                print(f"Ethernet: cliente conectado de {addr}")
            except OSError:
                pass

    def any(self):
        self._ensure_conn()
        return 0

    def read(self, n):
        self._ensure_conn()
        if self._conn is None:
            return None
        try:
            data = self._conn.recv(n)
            return data if data else None
        except OSError:
            self._conn = None
            return None

    def write(self, data):
        self._ensure_conn()
        if self._conn:
            try:
                self._conn.send(data)
            except OSError:
                self._conn = None


# ── WiFi STA ──────────────────────────────────────────────────
def connect_wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(config.WIFI_SSID, config.WIFI_PASS)
    print(f"Conectando em {config.WIFI_SSID}...", end="")
    for _ in range(30):
        if sta.isconnected():
            print(f" OK! IP={sta.ifconfig()[0]}")
            return True
        time.sleep(1)
        print(".", end="")
    print(" FALHA")
    return False


# ── Bridge task ───────────────────────────────────────────────
phys = None

async def run_bridge():
    print(f"Conectando ao bridge {config.AP_IP}:{config.BRIDGE_PORT}")
    reader, writer = await asyncio.open_connection(config.AP_IP, config.BRIDGE_PORT)
    print("Ponte estabelecida!")
    try:
        while True:
            # WiFi → interface física
            try:
                data = await asyncio.wait_for(reader.read(512), timeout=0.005)
                if not data:
                    break
                phys.write(data)
            except asyncio.TimeoutError:
                pass

            # Interface física → WiFi
            n = phys.any()
            if n:
                data = phys.read(n)
                if data:
                    writer.write(data)
                    await writer.drain()

            await asyncio.sleep_ms(1)
    except Exception as e:
        print(f"Erro na ponte: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    global phys

    if config.INTERFACE == "ETHERNET":
        phys = EthernetW5500()
    else:
        phys = RS485()

    while True:
        if connect_wifi():
            try:
                await run_bridge()
            except Exception as e:
                print(f"Erro: {e}")
        print("Reconectando em 5s...")
        await asyncio.sleep(5)


asyncio.run(main())
