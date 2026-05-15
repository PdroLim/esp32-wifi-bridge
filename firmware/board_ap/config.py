# Placa 1 - Access Point + Ethernet (ttyACM0)
WIFI_SSID    = "ESP32-BRIDGE"
WIFI_PASS    = "bridge12345"
BRIDGE_PORT  = 5000          # porta WiFi TCP (para placa STA)

ETH_MAC     = b"\x00\x08\xDC\x10\xB4\x1D"   # MAC único — Placa AP
ETH_IP      = "192.168.11.91"
ETH_MASK    = "255.255.255.0"
ETH_GW      = "192.168.11.1"
ETH_PORT    = 5001           # porta ETH TCP (dispositivo externo)

# Pinos SPI W5500 — Waveshare ESP32-S3-ETH-8DI-8RO
ETH_SPI_ID  = 2
ETH_CLK     = 15
ETH_MOSI    = 13
ETH_MISO    = 14
ETH_CS      = 16
ETH_RST     = 39
