import os
import sys
import subprocess
from littlefs import LittleFS

OFFSET   = 0x290000
FS_SIZE  = 0x180000
CRT_FILE = "root.crt"
BIN_FILE = "data.bin"
BAUD     = 921600


def detect_port():
    try:
        from serial.tools import list_ports
    except ImportError:
        print("ERROR: pyserial not found. Run 'pip install pyserial'.")
        sys.exit(1)

    ports = list(list_ports.comports())
    esp_ports = [
        p for p in ports
        if any(kw in (p.description or "").lower()
               for kw in ("cp210", "ch340", "ch341", "ftdi", "uart", "usb serial", "esp"))
    ]

    if not esp_ports and not ports:
        print("ERROR: No COM port found. Connect your ESP32 and try again.")
        sys.exit(1)

    candidates = esp_ports if esp_ports else ports

    if len(candidates) == 1:
        port = candidates[0].device
        print(f"Auto-detected port: {port}  ({candidates[0].description})")
        return port

    print("\nAvailable Ports:")
    for i, p in enumerate(candidates):
        print(f"    [{i}] {p.device}  —  {p.description}")
    while True:
        try:
            idx = int(input("\nSelect port number: "))
            if 0 <= idx < len(candidates):
                return candidates[idx].device
        except ValueError:
            pass
        print("    Please enter a valid number.")


def detect_esptool():
    for cmd in ("esptool.py", "esptool", sys.executable + " -m esptool"):
        parts = cmd.split()
        try:
            result = subprocess.run(
                parts + ["version"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"esptool found: {' '.join(parts)}")
                return parts
        except FileNotFoundError:
            continue

    print("ERROR: esptool not found. Run 'pip install esptool'.")
    sys.exit(1)


def create_image():
    print("\nCreating LittleFS image...")

    block_size  = 4096
    block_count = FS_SIZE // block_size

    fs = LittleFS(block_size=block_size, block_count=block_count, prog_size=256)

    with open(CRT_FILE, "rb") as f:
        data = f.read()

    with fs.open("/root.crt", "wb") as f:
        f.write(data)

    with open(BIN_FILE, "wb") as f:
        f.write(fs.context.buffer)

    size_kb = os.path.getsize(BIN_FILE) / 1024
    print(f"{BIN_FILE} created  ({size_kb:.1f} KB)")


def flash(port, esptool_cmd):
    print(f"\nFlashing to ESP32 ({port})...")

    cmd = esptool_cmd + [
        "--chip",  "esp32",
        "--port",  port,
        "--baud",  str(BAUD),
        "write_flash",
        hex(OFFSET), BIN_FILE,
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\nFlash successful. Please restart your ESP32.")
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Flash failed: {e}")
        sys.exit(1)


def cleanup():
    if os.path.exists(BIN_FILE):
        os.remove(BIN_FILE)
        print(f"Temp file '{BIN_FILE}' removed.")


if __name__ == "__main__":
    print("=" * 50)
    print("  ESP32 LittleFS Certificate Flasher")
    print("=" * 50)

    if not os.path.exists(CRT_FILE):
        print(f"ERROR: '{CRT_FILE}' not found. Place it in the same folder as this script.")
        sys.exit(1)

    try:
        port        = detect_port()
        esptool_cmd = detect_esptool()
        create_image()
        flash(port, esptool_cmd)
    finally:
        cleanup()
