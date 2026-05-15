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
        from machine import SPI, Pin
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

        # Servidor TCP interno para dispositivo externo
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
        if self._conn is None:
            return 0
        try:
            data = self._conn.recv(1)
            if data:
                self._buf = data + (self._buf if hasattr(self, "_buf") else b"")
                return len(self._buf)
        except OSError:
            pass
        return len(self._buf) if hasattr(self, "_buf") else 0

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


# ── WiFi AP ───────────────────────────────────────────────────
def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(ssid=config.WIFI_SSID, password=config.WIFI_PASS,
              security=3, channel=config.WIFI_CHANNEL)
    timeout = 10
    while not ap.active() and timeout > 0:
        time.sleep(0.5)
        timeout -= 1
    ip = ap.ifconfig()[0]
    print(f"AP ativo: ssid={config.WIFI_SSID} ip={ip} porta={config.BRIDGE_PORT}")
    return ip


# ── Bridge task ───────────────────────────────────────────────
phys = None

async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"WiFi cliente conectado: {addr}")
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
        print(f"Conexao encerrada: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
    print("Cliente desconectado")


async def main():
    global phys

    # Inicializar interface física
    if config.INTERFACE == "ETHERNET":
        phys = EthernetW5500()
    else:
        phys = RS485()

    # Inicializar WiFi AP
    setup_ap()

    # Servidor TCP para a placa STA
    server = await asyncio.start_server(handle_client, "0.0.0.0", config.BRIDGE_PORT)
    print("Ponte pronta. Aguardando placa STA...")
    await server.wait_closed()


asyncio.run(main())
