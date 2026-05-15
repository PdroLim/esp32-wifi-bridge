# ESP32-S3 WiFi Bridge

## Objetivo
Ponte WiFi transparente e bidirecional entre dois módulos Waveshare ESP32-S3-ETH-8DI-8RO.
Dados recebidos na porta RS485/Ethernet de uma placa são retransmitidos para a outra placa via WiFi.

## Hardware: Waveshare ESP32-S3-ETH-8DI-8RO

- ESP32-S3 dual-core 240MHz, 8MB PSRAM Octal
- 8 canais de relé controlados via PCA9554 I2C (endereço 0x20)
- RS485 isolada: TX=GPIO17, RX=GPIO18 (direção automática)
- Ethernet W5500 via SPI: CLK=GPIO15, MOSI=GPIO13, MISO=GPIO14, CS=GPIO16, RST=GPIO39
- WiFi 802.11b/g/n integrado no ESP32-S3

## Ambiente: Raspberry Pi 5
- Host: pi5@192.168.0.111
- Placa 1: /dev/ttyACM0
- Placa 2: /dev/ttyACM1
- esptool já instalado (v5.2.0)

## Arquitetura da Ponte

```
[Dispositivo A]
      |
   RS485/Ethernet
      |
[Placa 1 - AP (ttyACM0)]  <-- cria WiFi "ESP32-BRIDGE" (192.168.4.1)
      |
   WiFi TCP :5000
      |
[Placa 2 - STA (ttyACM1)] <-- conecta em "ESP32-BRIDGE"
      |
   RS485/Ethernet
      |
[Dispositivo B]
```

## Firmware: MicroPython

### Pré-requisitos

```bash
# Instalar mpremote no Pi
pip3 install mpremote --break-system-packages

# Baixar MicroPython para ESP32-S3 com 8MB PSRAM Octal
# URL: https://micropython.org/download/ESP32_GENERIC_S3/
# Arquivo: ESP32_GENERIC_S3-SPIRAM_OCT-vX.X.X.bin
wget https://micropython.org/resources/firmware/ESP32_GENERIC_S3-SPIRAM_OCT-20241025-v1.24.0.bin
```

### 1. Flash MicroPython (ambas as placas)

```bash
bash scripts/flash.sh /dev/ttyACM0 ESP32_GENERIC_S3-SPIRAM_OCT-20241025-v1.24.0.bin
bash scripts/flash.sh /dev/ttyACM1 ESP32_GENERIC_S3-SPIRAM_OCT-20241025-v1.24.0.bin
```

### 2. Deploy do Firmware

```bash
python3 scripts/deploy.py
```

O script:
1. Instala mpremote automaticamente
2. Faz upload de `config.py` e `main.py` para cada placa
3. Reinicia as placas

### 3. Verificar operação

```bash
# Ver log da placa AP
mpremote connect /dev/ttyACM0

# Ver log da placa STA
mpremote connect /dev/ttyACM1
```

## Configuração (config.py)

| Parâmetro | Placa AP | Placa STA | Descrição |
|---|---|---|---|
| WIFI_SSID | "ESP32-BRIDGE" | "ESP32-BRIDGE" | Nome da rede WiFi |
| WIFI_PASS | "bridge12345" | "bridge12345" | Senha da rede |
| BRIDGE_PORT | 5000 | - | Porta TCP da ponte |
| AP_IP | - | "192.168.4.1" | IP fixo da placa AP |
| UART_BAUD | 9600 | 9600 | Baud rate RS485 |
| INTERFACE | "RS485" | "RS485" | "RS485" ou "ETHERNET" |

## Modo Ethernet W5500 (opcional)

Para usar a porta RJ45 física ao invés de RS485:

```bash
# Instalar driver W5500
mpremote connect /dev/ttyACM0 mip install wiznet5k
mpremote connect /dev/ttyACM1 mip install wiznet5k
```

Alterar em `config.py`:
```python
INTERFACE = "ETHERNET"
ETH_IP = "192.168.1.100"   # AP board
ETH_IP = "192.168.1.101"   # STA board
```

**Nota:** O driver wiznet5k opera via SPI independentemente do WiFi. Ambos podem funcionar simultaneamente.

## Troubleshooting

- **Placa não aparece no /dev**: verificar cabo USB e permissões (`sudo usermod -a -G dialout pi5`)
- **Falha no flash**: usar `--baud 115200` no flash.sh para velocidade menor
- **STA não conecta**: verificar SSID/senha em config.py, placa AP deve iniciar primeiro
- **Dados corrompidos**: ajustar UART_BAUD para corresponder ao dispositivo externo

