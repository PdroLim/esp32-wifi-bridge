#!/usr/bin/env bash
# Flash MicroPython no ESP32-S3 (Waveshare ESP32-S3-ETH-8DI-8RO)
# Uso: bash scripts/flash.sh /dev/ttyACM0 firmware.bin

set -e

PORT="${1:-/dev/ttyACM0}"
FIRMWARE="${2:-ESP32_GENERIC_S3-SPIRAM_OCT-20241025-v1.24.0.bin}"

if [ ! -f "$FIRMWARE" ]; then
  echo "Firmware nao encontrado: $FIRMWARE"
  echo "Baixe em: https://micropython.org/download/ESP32_GENERIC_S3/"
  echo "Arquivo: ESP32_GENERIC_S3-SPIRAM_OCT-*.bin"
  exit 1
fi

echo "=== Flash MicroPython ==="
echo "Porta   : $PORT"
echo "Firmware: $FIRMWARE"
echo ""

echo "[1/2] Apagando flash..."
esptool --chip esp32s3 --port "$PORT" --baud 460800 erase_flash

echo "[2/2] Gravando firmware..."
esptool --chip esp32s3 --port "$PORT" --baud 460800 \
  write_flash -z 0x0 "$FIRMWARE"

echo ""
echo "Flash concluido em $PORT!"
