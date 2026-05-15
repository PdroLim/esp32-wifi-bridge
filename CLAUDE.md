# ESP32-S3 WiFi Bridge

## Objetivo
Ponte WiFi transparente e bidirecional entre dois módulos Waveshare ESP32-S3-ETH-8DI-8RO.
Dados TCP recebidos na porta Ethernet de uma placa são retransmitidos para a outra via WiFi.

## Hardware: Waveshare ESP32-S3-ETH-8DI-8RO

- ESP32-S3 dual-core 240MHz, 8MB PSRAM Octal
- W5500 Ethernet via SPI: CLK=GPIO15, MOSI=GPIO13, MISO=GPIO14, CS=GPIO16, RST=GPIO39
- RS485 isolada: TX=GPIO17, RX=GPIO18
- WiFi 802.11b/g/n integrado

## Ambiente: Raspberry Pi 5

- Host: pi5@192.168.0.111
- Placa AP  (ttyACM0): MAC WiFi 10:B4:1D:CC:93:F0
- Placa STA (ttyACM1): MAC WiFi 98:A3:16:DC:2D:D8
- mpremote: `~/.local/bin/mpremote` → `export PATH="$PATH:/home/pi5/.local/bin"`

## Arquitetura

```
[Rede 192.168.11.x]
        |
  ETH 192.168.11.91
        |
[Placa AP — ttyACM0]  ←── cria WiFi "ESP32-BRIDGE" (192.168.4.1)
        |
   WiFi TCP :5000
        |
[Placa STA — ttyACM1] ←── conecta em "ESP32-BRIDGE" (192.168.4.2)
        |
  ETH 192.168.11.92
        |
[Rede 192.168.11.x / Notebook]
```

Dados TCP chegam em `IP:5001` de uma placa e são encaminhados
transparentemente para a outra via WiFi e retransmitidos na porta ETH.

## IPs de Produção

| Placa | ETH IP | ETH MAC | WiFi IP |
|---|---|---|---|
| AP  (ttyACM0) | 192.168.11.91 | 00:08:DC:10:B4:1D | 192.168.4.1 |
| STA (ttyACM1) | 192.168.11.92 | 00:08:DC:98:A3:16 | 192.168.4.2 |

Gateway padrão: 192.168.11.1

## Firmware: MicroPython v1.24.0

Gravado: `ESP32_GENERIC_S3-SPIRAM_OCT-20241025-v1.24.0.bin`

### Re-deploy (após qualquer mudança de config)

```bash
export PATH="$PATH:/home/pi5/.local/bin"
cd ~/esp32-wifi-bridge

# Placa AP
mpremote connect /dev/ttyACM0 fs cp firmware/board_ap/config.py  :config.py
mpremote connect /dev/ttyACM0 fs cp firmware/board_ap/main.py    :main.py
mpremote connect /dev/ttyACM0 fs cp firmware/w5500.py            :w5500.py
mpremote connect /dev/ttyACM0 reset

# Placa STA
mpremote connect /dev/ttyACM1 fs cp firmware/board_sta/config.py :config.py
mpremote connect /dev/ttyACM1 fs cp firmware/board_sta/main.py   :main.py
mpremote connect /dev/ttyACM1 fs cp firmware/w5500.py            :w5500.py
mpremote connect /dev/ttyACM1 reset
```

### Monitorar logs

```bash
export PATH="$PATH:/home/pi5/.local/bin"
mpremote connect /dev/ttyACM0   # Placa AP  (Ctrl+X para sair)
mpremote connect /dev/ttyACM1   # Placa STA (Ctrl+X para sair)
```

**Log esperado AP:**
```
W5500 version: 0x04 OK
ETH up: 192.168.11.91
ETH aguardando em 192.168.11.91:5001
WiFi AP: ESP32-BRIDGE  IP=192.168.4.1
Pronto — aguardando STA WiFi e cliente ETH
STA conectou via WiFi: (192.168.4.2, XXXXX)
ETH: cliente conectou
```

**Log esperado STA:**
```
W5500 version: 0x04 OK
ETH up: 192.168.11.92
ETH aguardando em 192.168.11.92:5001
Conectando em ESP32-BRIDGE.. OK → 192.168.4.2
WiFi bridge: 192.168.4.1:5000
ETH: cliente conectou
```

### Verificar ping (do notebook ou de outro dispositivo na rede 192.168.11.x)

```
ping 192.168.11.91   ← Placa AP
ping 192.168.11.92   ← Placa STA
```

### Conectar para bridging de dados

```
# Dispositivo A conecta em:
TCP → 192.168.11.91:5001

# Dispositivo B conecta em:
TCP → 192.168.11.92:5001

# Dados fluem de forma transparente entre A e B via WiFi
```

## Alterar configuração

Editar `firmware/board_ap/config.py` e/ou `firmware/board_sta/config.py`:

| Parâmetro | Descrição |
|---|---|
| `ETH_IP` | IP da porta Ethernet desta placa |
| `ETH_GW` | Gateway da rede Ethernet |
| `ETH_PORT` | Porta TCP que o dispositivo externo conecta (padrão: 5001) |
| `WIFI_SSID` / `WIFI_PASS` | Credenciais do hotspot WiFi interno |
| `BRIDGE_PORT` | Porta TCP interna do bridge WiFi (padrão: 5000) |

Após editar, re-fazer o deploy da placa afetada.

## Troubleshooting

| Sintoma | Causa | Solução |
|---|---|---|
| `W5500 version: 0xFF` | Pinos SPI errados ou sem alimentação | Verificar `ETH_CLK/MOSI/MISO/CS/RST` no config |
| `ETH: sem link` | Cabo não conectado | Conectar cabo Ethernet |
| Ping não responde | IP na subnet errada | Verificar que o dispositivo está na mesma rede |
| STA não conecta WiFi | AP não iniciou | Iniciar placa AP primeiro; verificar SSID/senha |
| `mpremote: port in use` | Processo anterior travado | `pkill -f mpremote` no Pi |
