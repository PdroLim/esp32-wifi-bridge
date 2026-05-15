#!/usr/bin/env python3
"""Deploy do firmware de ponte WiFi nas duas placas ESP32-S3."""

import subprocess
import sys
import os
import time


def run(cmd, check=True):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    if check and result.returncode != 0:
        raise RuntimeError(f"Comando falhou: {cmd}")
    return result.returncode == 0


def upload_file(port, local, remote):
    cmd = f"mpremote connect {port} fs cp {local} :{remote}"
    return run(cmd)


def deploy(port, role):
    fw_dir = os.path.join(os.path.dirname(__file__), "..", "firmware", f"board_{role}")
    fw_dir = os.path.normpath(fw_dir)

    print(f"\n{=*50}")
    print(f"Fazendo deploy da placa {role.upper()} em {port}")
    print(f"{=*50}")

    for filename in ["config.py", "main.py"]:
        local = os.path.join(fw_dir, filename)
        if not os.path.exists(local):
            raise FileNotFoundError(f"Arquivo nao encontrado: {local}")
        print(f"\nUpload {filename}...")
        upload_file(port, local, filename)

    print(f"\nReiniciando {port}...")
    run(f"mpremote connect {port} reset", check=False)
    time.sleep(2)
    print(f"Placa {role.upper()} pronta!")


def main():
    print("=== Deploy ESP32 WiFi Bridge ===\n")

    # Instalar mpremote se necessario
    try:
        run("mpremote version", check=True)
    except Exception:
        print("Instalando mpremote...")
        run("pip3 install mpremote --break-system-packages")

    deploy("/dev/ttyACM0", "ap")
    deploy("/dev/ttyACM1", "sta")

    print(f"\n{=*50}")
    print("Deploy concluido!")
    print("Para monitorar os logs:")
    print("  mpremote connect /dev/ttyACM0   <- Placa AP")
    print("  mpremote connect /dev/ttyACM1   <- Placa STA")
    print(f"{=*50}")


if __name__ == "__main__":
    main()
