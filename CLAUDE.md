# ESP32-S3 WiFi Bridge

## Objetivo
Ponte WiFi transparente e bidirecional entre dois módulos Waveshare ESP32-S3-ETH-8DI-8RO.
Dados recebidos na porta RS485/Ethernet de uma placa são retransmitidos para a outra placa via WiFi.

## Hardware: Waveshare ESP32-S3-ETH-8DI-8RO

- ESP32-S3 dual-core 240MHz, 8MB PSRAM Octal
- 8 canais de relé controlados via PCA9554 I2C (endereço 0x20)
- RS485 isolada: TX=GPIO17, RX=GPIO18 (direção automática — sem pino DE/RE)
- Ethernet W5500 via SPI: CLK=GPIO15, MOSI=GPIO13, MISO=GPIO14, CS=GPIO16, RST=GPIO39
- WiFi 802.11b/g/n integrado no ESP32-S3

## Ambiente: Raspberry Pi 5
- Host: pi5@192.168.0.111
- Placa 1 (AP): /dev/ttyACM0  — MAC: 10:B4:1D:CC:93:F0
- Placa 2 (STA): /dev/ttyACM1 — MAC: 98:A3:16:DC:2D:D8
- esptool instalado: v5.2.0
- mpremote instalado em: ~/.local/bin/mpremote
  → Adicionar ao PATH: `export PATH="$PATH:/home/pi5/.local/bin"`

## Arquitetura da Ponte

```
[Dispositivo A]
      |
   RS485 (GPIO17/18)
      |
[Placa 1 - AP  /dev/ttyACM0]  ← cria WiFi "ESP32-BRIDGE" pw:bridge12345 @ 192.168.4.1
      |
   TCP WiFi :5000
      |
[Placa 2 - STA /dev/ttyACM1] ← conecta em "ESP32-BRIDGE" @ 192.168.4.2
      |
   RS485 (GPIO17/18)
      |
[Dispositivo B]
```

## Firmware: MicroPython v1.24.0

Gravado em: `ESP32_GENERIC_S3-SPIRAM_OCT-20241025-v1.24.0.bin`

### Pré-requisitos

```bash
# mpremote (já instalado)
export PATH="$PATH:/home/pi5/.local/bin"

# Baixar firmware MicroPython para ESP32-S3 SPIRAM Octal
cd ~
wget https://micropython.org/resources/firmware/ESP32_GENERIC_S3-SPIRAM_OCT-20241025-v1.24.0.bin -O esp32s3_fw.bin
```

### 1. Flash MicroPython (já executado com sucesso)

```bash
export PATH="$PATH:/home/pi5/.local/bin"

# Placa 1 AP (ttyACM0)
esptool --chip esp32s3 --port /dev/ttyACM0 --baud 460800 erase_flash
esptool --chip esp32s3 --port /dev/ttyACM0 --baud 460800 write_flash -z 0x0 ~/esp32s3_fw.bin

# Placa 2 STA (ttyACM1)
esptool --chip esp32s3 --port /dev/ttyACM1 --baud 460800 erase_flash
esptool --chip esp32s3 --port /dev/ttyACM1 --baud 460800 write_flash -z 0x0 ~/esp32s3_fw.bin
```

### 2. Deploy do Firmware (já executado com sucesso)

```bash
export PATH="$PATH:/home/pi5/.local/bin"

# Placa AP
mpremote connect /dev/ttyACM0 fs cp firmware/board_ap/config.py :config.py
mpremote connect /dev/ttyACM0 fs cp firmware/board_ap/main.py :main.py

# Placa STA
mpremote connect /dev/ttyACM1 fs cp firmware/board_sta/config.py :config.py
mpremote connect /dev/ttyACM1 fs cp firmware/board_sta/main.py :main.py
```

Ou usar o script:
```bash
cd ~/esp32-wifi-bridge && python3 scripts/deploy.py
```

### 3. Verificar operação

```bash
export PATH="$PATH:/home/pi5/.local/bin"

# Scan WiFi - deve ver "ESP32-BRIDGE"
iw dev wlan0 scan | grep ESP32-BRIDGE

# Ver log das placas (Ctrl+C para sair)
mpremote connect /dev/ttyACM0   # Placa AP
mpremote connect /dev/ttyACM1   # Placa STA
```

**Log esperado Placa AP:**
```
RS485 UART2 TX=17 RX=18 9600bps
AP ativo: ssid=ESP32-BRIDGE ip=192.168.4.1 porta=5000
Ponte pronta. Aguardando placa STA...
WiFi cliente conectado: (192.168.4.2, XXXXX)
```

**Log esperado Placa STA:**
```
RS485 UART2 TX=17 RX=18 9600bps
Conectando em ESP32-BRIDGE..... OK! IP=192.168.4.2
Conectando ao bridge 192.168.4.1:5000
Ponte estabelecida!
```

## Configuração (config.py)

| Parâmetro | Placa AP | Placa STA | Descrição |
|---|---|---|---|
| WIFI_SSID | "ESP32-BRIDGE" | "ESP32-BRIDGE" | Nome da rede WiFi |
| WIFI_PASS | "bridge12345" | "bridge12345" | Senha da rede |
| BRIDGE_PORT | 5000 | — | Porta TCP da ponte |
| AP_IP | — | "192.168.4.1" | IP fixo da placa AP |
| UART_BAUD | 9600 | 9600 | Baud rate RS485 |
| INTERFACE | "RS485" | "RS485" | "RS485" ou "ETHERNET" |

## Modo Ethernet W5500 (opcional)

Para usar a porta RJ45 física ao invés de RS485, altere em `config.py`:

```python
INTERFACE = "ETHERNET"
ETH_IP = "192.168.1.100"   # AP board
# ETH_IP = "192.168.1.101"   # STA board
```

Instalar driver W5500:
```bash
mpremote connect /dev/ttyACM0 mip install wiznet5k
mpremote connect /dev/ttyACM1 mip install wiznet5k
```

**Nota:** O driver W5500 opera via SPI separado da stack WiFi do ESP32-S3.

## Troubleshooting

- **mpremote não encontrado**: `export PATH="$PATH:/home/pi5/.local/bin"`
- **Placa não aparece**: verificar USB (`ls /dev/ttyACM*`)
- **Falha no flash**: tentar `--baud 115200` para velocidade menor
- **STA não conecta**: placa AP deve iniciar primeiro; verificar SSID/senha
- **Dados corrompidos**: ajustar `UART_BAUD` para o dispositivo externo
- **Reconexão automática**: placa STA reconecta sozinha em caso de queda WiFi
