import network
import uasyncio as asyncio
import time
import config
from machine import SPI, Pin
from w5500 import W5500

nic = None
_eth = None

# ── Ethernet ─────────────────────────────────────────────────
def eth_init():
    global nic
    spi = SPI(config.ETH_SPI_ID, baudrate=10_000_000,
              sck=Pin(config.ETH_CLK), mosi=Pin(config.ETH_MOSI), miso=Pin(config.ETH_MISO))
    cs  = Pin(config.ETH_CS,  Pin.OUT)
    rst = Pin(config.ETH_RST, Pin.OUT)
    nic = W5500(spi, cs, rst, mac=config.ETH_MAC)
    nic.ifconfig(config.ETH_IP, config.ETH_MASK, config.ETH_GW)
    for _ in range(100):
        if nic.link_up():
            print(f"ETH up: {config.ETH_IP}")
            return
        time.sleep_ms(100)
    print("ETH: sem link (verifique o cabo)")

def eth_open_server():
    global _eth
    if _eth:
        try: _eth.close()
        except: pass
    _eth = nic.socket(0)
    _eth.bind(config.ETH_PORT)
    _eth.listen()
    print(f"ETH aguardando em {config.ETH_IP}:{config.ETH_PORT}")

# ── WiFi STA ──────────────────────────────────────────────────
def wifi_connect():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if sta.isconnected():
        return True
    sta.connect(config.WIFI_SSID, config.WIFI_PASS)
    print(f"Conectando em {config.WIFI_SSID}", end="")
    for _ in range(30):
        if sta.isconnected():
            print(f" OK → {sta.ifconfig()[0]}")
            return True
        time.sleep(1)
        print(".", end="")
    print(" FALHOU")
    return False

# ── Bridge ────────────────────────────────────────────────────
async def run_bridge():
    global _eth
    wifi_r, wifi_w = await asyncio.open_connection(config.AP_IP, config.BRIDGE_PORT)
    print(f"WiFi bridge: {config.AP_IP}:{config.BRIDGE_PORT}")
    eth_up = False

    try:
        while True:
            # Aguarda cliente ETH
            if not eth_up:
                if _eth.accept_ready():
                    eth_up = True
                    print("ETH: cliente conectou")
                else:
                    await asyncio.sleep_ms(50)
                    continue

            # ETH → WiFi
            n = _eth.available()
            if n:
                chunk = _eth.recv(min(n, 512))
                if chunk:
                    wifi_w.write(chunk)
                    await wifi_w.drain()

            # WiFi → ETH
            try:
                chunk = await asyncio.wait_for(wifi_r.read(512), timeout=0.005)
                if not chunk:
                    break
                _eth.send(chunk)
            except asyncio.TimeoutError:
                pass

            if not _eth.is_connected():
                print("ETH: cliente desconectou")
                eth_open_server()
                eth_up = False

            await asyncio.sleep_ms(1)

    except Exception as e:
        print(f"Bridge encerrada: {e}")
    finally:
        try:
            wifi_w.close()
            await wifi_w.wait_closed()
        except: pass
        eth_open_server()

async def main():
    eth_init()
    eth_open_server()
    while True:
        if wifi_connect():
            try:
                await run_bridge()
            except Exception as e:
                print(f"Erro: {e}")
        print("Reconectando em 5s...")
        await asyncio.sleep(5)

asyncio.run(main())