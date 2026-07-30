# PortHack-S3

This project is an interactive, retro-themed cybersecurity diagnostic and simulation dashboard designed to run in a 240x135 frame buffer, matching the exact physical screen resolution of the M5Stack Cardputer Adv. 

It is written in both **Python (Pygame)** for desktop testing and **C++ (Arduino framework)** for compiling directly onto physical ESP32-S3 hardware.

## What is this?
It is a virtual handheld "multitool" emulator (similar to a Flipper Zero interface) that lets you interact with local networks, decrypt simple hashes using on-chip cryptographic hardware, and explore hardware specs.

### Integrated Modules:
1. **Wi-Fi Recon:** Performs real Wi-Fi network scans (using the ESP32’s actual antenna) or local subnet IP probes (on desktop Python) to list active host channels.
2. **MD5 Cracker:** An alphanumeric `[a-zA-Z0-9]` brute-force decryption tool that utilizes high-speed cryptographic libraries (`mbedtls` on the ESP32) to crack 1-to-4 character hashes.
3. **Traffic Sniffer:** Simulates packet sniffing telemetry feeds (or accesses raw local sockets on rooted desktops) to monitor active network traffic.
4. **IR-Clone:** Simulates capturing, decoding, and saving 38kHz infrared carrier signals to flash memory.
5. **System Diagnostics:** Displays live hardware metrics such as active CPU frequency, available heap RAM, flash capacity, and silicon chip revision.

---

## Setup

### 1. Running the Python Desktop Emulator (VS Code)
Requires Python 3 and Pygame.

```bash
# Install Pygame
pip install pygame

# Run the app
python main.py
