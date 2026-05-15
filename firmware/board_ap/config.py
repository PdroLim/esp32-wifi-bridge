# Configuração: Placa 1 - Access Point (ttyACM0)

ROLE = "AP"

# WiFi - cria hotspot
WIFI_SSID = "ESP32-BRIDGE"
WIFI_PASS = "bridge12345"
WIFI_CHANNEL = 6
BRIDGE_PORT = 5000

# Interface física: "RS485" ou "ETHERNET"
INTERFACE = "RS485"

# RS485 UART (GPIO17=TX, GPIO18=RX - automático, sem pino DE/RE)
UART_ID = 2
UART_TX = 17
UART_RX = 18
UART_BAUD = 9600
UART_BITS = 8
UART_PARITY = None
UART_STOP = 1

# Ethernet W5500 via SPI (ativo quando INTERFACE = "ETHERNET")
ETH_SPI_ID = 2
ETH_CLK  = 15
ETH_MOSI = 13
ETH_MISO = 14
ETH_CS   = 16
ETH_RST  = 39
ETH_IP      = "192.168.1.100"
ETH_MASK    = "255.255.255.0"
ETH_GW      = "192.168.1.1"
ETH_PORT    = 5001
