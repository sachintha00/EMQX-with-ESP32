import subprocess
import sys
from serial.tools import list_ports

ports = list(list_ports.comports())
esp_ports = [p for p in ports if any(kw in (p.description or "").lower()
             for kw in ("cp210", "ch340", "ftdi", "uart", "usb serial", "esp"))]

port = esp_ports[0].device if esp_ports else ports[0].device
print(f"Found: {port}")

subprocess.run([
    "esptool", "--chip", "esp32",
    "--port", port,
    "erase_flash"
], check=True)

print("Flash erased successfully!")
