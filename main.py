import sys
import os
import time
import socket
import threading
import hashlib
import string
import itertools
import pygame

# Initialize Pygame
pygame.init()
pygame.key.set_repeat(200, 50)

V_WIDTH, V_HEIGHT = 240, 135
SCALE = 4  
WINDOW_WIDTH, WINDOW_HEIGHT = V_WIDTH * SCALE, V_HEIGHT * SCALE

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("PortHack-S3 - Cardputer Emulator")
virtual_screen = pygame.Surface((V_WIDTH, V_HEIGHT))
clock = pygame.time.Clock()

try:
    font = pygame.font.SysFont("Courier New", 10, bold=True)
except Exception:
    font = pygame.font.Font(None, 12)

COLOR_BG = (10, 16, 10)
COLOR_TEXT = (57, 255, 20)
COLOR_ACCENT = (0, 150, 0)
COLOR_WHITE = (220, 220, 220)
COLOR_RED = (255, 50, 50)

current_state = "MENU"
menu_index = 0
menu_items = ["1. NET RECON", "2. HASH CRACK", "3. SNIFFER", "4. IR CLONE", "5. SYS INFO"]

scanning = False
scan_results = []
input_buffer = ""
typing_active = False

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def thread_network_recon():
    global scanning, scan_results
    scanning = True
    scan_results = ["Probing subnet...", "Searching active IPs..."]
    local_ip = get_local_ip()
    parts = local_ip.split('.')
    if len(parts) == 4:
        subnet = f"{parts[0]}.{parts[1]}.{parts[2]}."
        for i in range(1, 26):
            if not scanning:
                break
            ip = f"{subnet}{i}"
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            res = s.connect_ex((ip, 80))
            if res == 0:
                scan_results.append(f"-> {ip} : Active (HTTP)")
            else:
                s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s2.settimeout(0.1)
                res2 = s2.connect_ex((ip, 135))
                if res2 == 0:
                     scan_results.append(f"-> {ip} : Active (NetBIOS)")
                s2.close()
            s.close()
    scan_results.append("Scan completed.")
    scanning = False

def thread_hash_crack(target_hash):
    global scanning, scan_results
    scanning = True
    scan_results = [f"Target: {target_hash[:8]}...", "Cracking: [a-zA-Z0-9] up to 4..."]
    
    # Combined alphabet: a-z, A-Z, 0-9 (62 characters)
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    found = False
    start_time = time.time()
    
    for length in range(1, 5):
        if found or not scanning:
            break
        scan_results.append(f"Trying length {length}...")
        for guess in itertools.product(chars, repeat=length):
            if not scanning:
                break
            guess_str = "".join(guess)
            guess_hash = hashlib.md5(guess_str.encode()).hexdigest()
            if guess_hash.lower() == target_hash.lower():
                elapsed = time.time() - start_time
                scan_results.append("SUCCESS!")
                scan_results.append(f"Match: '{guess_str}'")
                scan_results.append(f"Time: {elapsed:.2f}s")
                with open("virtual_sd.txt", "a") as f:
                    f.write(f"Cracked {target_hash} -> {guess_str}\n")
                found = True
                break
                
    if not found and scanning:
        scan_results.append("Finished (No match).")
    scanning = False

def thread_packet_sniffer():
    global scanning, scan_results
    scanning = True
    scan_results = ["Initializing Sniffer..."]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        s.settimeout(1.0)
        scan_results.append("Sniffing live TCP traffic:")
        while scanning:
            try:
                packet, addr = s.recvfrom(65565)
                scan_results.append(f"TCP {addr[0]} -> Recv {len(packet)}B")
                if len(scan_results) > 10:
                    scan_results.pop(1)
            except socket.timeout:
                continue
    except OSError:
        scan_results.append("Admin/Root block. Running simulated")
        scan_results.append("telemetry:")
        import random
        while scanning:
            time.sleep(random.uniform(0.3, 0.9))
            mock_ips = ["192.168.1.1", "192.168.1.10", "8.8.8.8", "104.244.42.1"]
            src = random.choice(mock_ips)
            dst = get_local_ip()
            proto = random.choice(["TCP", "UDP", "DNS", "HTTPS"])
            port = random.randint(80, 8080)
            scan_results.append(f"[{proto}] {src} -> {dst}:{port}")
            if len(scan_results) > 9:
                scan_results.pop(2)
    scanning = False

def draw_text(surface, text, x, y, color=COLOR_TEXT):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

running = True
captured_ir_code = ""

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            scanning = False
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                scanning = False
                current_state = "MENU"
                
            elif current_state == "MENU":
                if event.key == pygame.K_UP:
                    menu_index = (menu_index - 1) % len(menu_items)
                elif event.key == pygame.K_DOWN:
                    menu_index = (menu_index + 1) % len(menu_items)
                elif event.key == pygame.K_RETURN:
                    if menu_index == 0:
                        current_state = "NETSCAN"
                        scan_results = []
                        threading.Thread(target=thread_network_recon, daemon=True).start()
                    elif menu_index == 1:
                        current_state = "HASHCRACK"
                        input_buffer = "81dc9bdb52d04dc20036dbd8313ed055" 
                        typing_active = True
                        scan_results = []
                    elif menu_index == 2:
                        current_state = "SNIFFER"
                        scan_results = []
                        threading.Thread(target=thread_packet_sniffer, daemon=True).start()
                    elif menu_index == 3:
                        current_state = "IRCLONE"
                        captured_ir_code = ""
                    elif menu_index == 4:
                        current_state = "SYSINFO"
                        
            elif current_state == "HASHCRACK" and typing_active:
                if event.key == pygame.K_RETURN:
                    typing_active = False
                    threading.Thread(target=thread_hash_crack, args=(input_buffer,), daemon=True).start()
                elif event.key == pygame.K_BACKSPACE:
                    input_buffer = input_buffer[:-1]
                else:
                    if len(input_buffer) < 32 and event.unicode in "0123456789abcdefABCDEF":
                        input_buffer += event.unicode.lower()

            elif current_state == "IRCLONE":
                if event.key != pygame.K_ESCAPE and not captured_ir_code:
                    raw_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8].upper()
                    captured_ir_code = f"NEC 0x{raw_hash}"
                    with open("virtual_sd.txt", "a") as f:
                        f.write(f"IR Captured: {captured_ir_code}\n")

    virtual_screen.fill(COLOR_BG)
    pygame.draw.rect(virtual_screen, COLOR_ACCENT, (0, 0, V_WIDTH, 12))
    draw_text(virtual_screen, f"PORTHACK-S3  v1.0.0", 4, 1, COLOR_WHITE)
    draw_text(virtual_screen, "[ESC] BACK", 185, 1, COLOR_WHITE)
    
    if current_state == "MENU":
        draw_text(virtual_screen, "=== CHOOSE SYSTEM MODULE ===", 10, 18, COLOR_ACCENT)
        for i, item in enumerate(menu_items):
            color = COLOR_WHITE if i == menu_index else COLOR_TEXT
            prefix = " > " if i == menu_index else "   "
            draw_text(virtual_screen, f"{prefix}{item}", 10, 36 + (i * 14), color)
        draw_text(virtual_screen, "Use UP/DOWN keys & PRESS [ENTER]", 10, 115, COLOR_ACCENT)
        
    elif current_state == "NETSCAN":
        draw_text(virtual_screen, "MODULE: LOCAL IP SCANNER", 10, 16, COLOR_WHITE)
        y_offset = 32
        for line in scan_results[-8:]:
            draw_text(virtual_screen, line, 10, y_offset)
            y_offset += 11
            
    elif current_state == "HASHCRACK":
        draw_text(virtual_screen, "MODULE: MD5 CRACKER TOOL", 10, 16, COLOR_WHITE)
        if typing_active:
            draw_text(virtual_screen, "INPUT TARGET MD5 HASH:", 10, 32, COLOR_ACCENT)
            pygame.draw.rect(virtual_screen, (20, 40, 20), (10, 44, 220, 14))
            draw_text(virtual_screen, input_buffer + ("|" if time.time() % 1 > 0.5 else ""), 12, 46, COLOR_WHITE)
            draw_text(virtual_screen, "Press [ENTER] to execute", 10, 64, COLOR_TEXT)
        else:
            y_offset = 32
            for line in scan_results[-8:]:
                draw_text(virtual_screen, line, 10, y_offset)
                y_offset += 11
                
    elif current_state == "SNIFFER":
        draw_text(virtual_screen, "MODULE: TCP PACKET SNIFFER", 10, 16, COLOR_WHITE)
        y_offset = 32
        for line in scan_results[-8:]:
            draw_text(virtual_screen, line, 10, y_offset)
            y_offset += 11
            
    elif current_state == "IRCLONE":
        draw_text(virtual_screen, "MODULE: INFRARED CLONER", 10, 16, COLOR_WHITE)
        if not captured_ir_code:
            draw_text(virtual_screen, "[WAITING FOR IR CARRIER WAVE]", 10, 45, COLOR_RED)
            draw_text(virtual_screen, "Press any key to capture a raw IR signal...", 10, 65, COLOR_TEXT)
        else:
            draw_text(virtual_screen, "SIGNAL ACQUIRED!", 10, 35, COLOR_WHITE)
            draw_text(virtual_screen, f"Saved Code: {captured_ir_code}", 10, 55, COLOR_TEXT)
            draw_text(virtual_screen, "Replaying carrier frequency (38kHz)", 10, 75, COLOR_ACCENT)
            draw_text(virtual_screen, "Saved to virtual_sd.txt!", 10, 95, COLOR_WHITE)
            
    elif current_state == "SYSINFO":
        draw_text(virtual_screen, "MODULE: HARDWARE DIAGNOSTIC", 10, 16, COLOR_WHITE)
        draw_text(virtual_screen, f"CPU Emulation: ESP32-S3 @ 240MHz", 10, 32, COLOR_TEXT)
        draw_text(virtual_screen, f"Local IP Address: {get_local_ip()}", 10, 47, COLOR_TEXT)
        draw_text(virtual_screen, f"Virtual Flash Storage: 4.0 MB", 10, 62, COLOR_TEXT)
        draw_text(virtual_screen, f"Memory Allocation: < 512 KB RAM", 10, 77, COLOR_TEXT)
        draw_text(virtual_screen, f"OS Target: FreeRTOS / ESP-IDF", 10, 92, COLOR_TEXT)
        draw_text(virtual_screen, f"SD Card: virtual_sd.txt (ACTIVE)", 10, 107, COLOR_ACCENT)

    scaled_surface = pygame.transform.scale(virtual_screen, (WINDOW_WIDTH, WINDOW_HEIGHT))
    screen.blit(scaled_surface, (0, 0))
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()