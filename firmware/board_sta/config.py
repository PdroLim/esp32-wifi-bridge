# Placa 2 - Station + Ethernet (ttyACM1)
WIFI_SSID    = "ESP32-BRIDGE"
WIFI_PASS    = "bridge12345"
AP_IP        = "192.168.4.1"   # IP fixo da Placa AP no WiFi interno
BRIDGE_PORT  = 5000

ETH_MAC     = b"\x00\x08\xDC\x98\xA3\x16"   # MAC único — Placa STA
ETH_IP      = "192.168.11.92"
ETH_MASK    = "255.255.255.0"
ETH_GW      = "192.168.11.1"
ETH_PORT    = 5001

# Pinos SPI W5500 — Waveshare ESP32-S3-ETH-8DI-8RO
ETH_SPI_ID  = 2
ETH_CLK     = 15
ETH_MOSI    = 13
ETH_MISO    = 14
ETH_CS      = 16
ETH_RST     = 39
