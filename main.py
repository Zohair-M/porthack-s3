# ------------------------------------------------------------------------------
# STEP 1: IMPORTING LIBRARIES (The Tools We Need)
# ------------------------------------------------------------------------------

import sys        # Allows us to interact with the system (like closing the app completely).
import os         # Gives us access to files and folders on your computer.
import time       # Helps the computer measure time, add delays, or track timestamps.
import socket     # The networking toolbox. It lets our computer talk to the internet and routers.
import threading  # Allows multitasking. This lets the computer run background tasks without freezing the screen.
import hashlib    # A security toolbox. It handles encryption, hashing, and password math.
import pygame     # Our visual toolbox. It draws the windows, handles colors, and detects keyboard presses.
import random    # A tool to generate random numbers (used for simulating coordinates and network messages).

# ------------------------------------------------------------------------------
# STEP 2: SETTING UP THE EMULATED SCREEN
# ------------------------------------------------------------------------------
# Pygame needs to know how big to make our screen. The real Cardputer screen 
# is tiny—just 240 pixels wide by 135 pixels tall. 

pygame.init() # This "starts the engine" of Pygame so we can use its graphics tools.

# We set up a rule: if you hold down a key on your keyboard, it will repeat.
# 200 is the delay before repeating (in milliseconds), 50 is how fast it repeats.
pygame.key.set_repeat(200, 50)

# We define the physical pixel resolution of the real M5Stack Cardputer.
V_WIDTH = 240   # Virtual Width: 240 pixels.
V_HEIGHT = 135  # Virtual Height: 135 pixels.

# Because a 240x135 window is tiny on a modern computer screen, we scale it up.
# "SCALE = 4" means we will multiply the size by 4, making it 960x540 so it's easy to read.
SCALE = 4  
WINDOW_WIDTH = V_WIDTH * SCALE   # 240 * 4 = 960 pixels wide.
WINDOW_HEIGHT = V_HEIGHT * SCALE # 135 * 4 = 540 pixels tall.

# Create the desktop window using our upscaled measurements.
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("PortHack-S3 - Cardputer Emulator") # Sets the window title.

# We also create a "virtual surface". This is an invisible, tiny drawing board 
# that is exactly 240x135. We draw our text here first, then stretch it to the main window.
virtual_screen = pygame.Surface((V_WIDTH, V_HEIGHT))

# The "clock" will help us control how fast our program runs (frames per second).
clock = pygame.time.Clock()

# ------------------------------------------------------------------------------
# STEP 3: LOADING FONTS AND COLORS
# ------------------------------------------------------------------------------
# To display text on our retro screen, we need to load a font. 
# We use a "try / except" block. It tells the computer: "Try to do this, but if 
# it crashes or fails, do this fallback option instead so the program doesn't close."
try:
    # Try to load "Courier New" (a classic coder font) at size 10, in bold.
    font = pygame.font.SysFont("Courier New", 10, bold=True)
except Exception:
    # If the user doesn't have Courier New, load Pygame's basic default font at size 12.
    font = pygame.font.Font(None, 12)

# Colors in programming are defined by mixing Red, Green, and Blue (RGB) from 0 to 255.
# (0, 0, 0) is pure black. (255, 255, 255) is pure white.
COLOR_BG = (10, 16, 10)       # Dark Green (Background color)
COLOR_TEXT = (57, 255, 20)     # Neon Green (Classic hacker text)
COLOR_ACCENT = (0, 150, 0)     # Medium Green (For buttons and borders)
COLOR_WHITE = (220, 220, 220)  # Off-White (For clear titles)
COLOR_RED = (255, 50, 50)      # Red (For alert and warning messages)

# ------------------------------------------------------------------------------
# STEP 4: DEFINING STATE VARIABLES (Where are we in the app?)
# ------------------------------------------------------------------------------
# Variables are boxes where we store information.
# "current_state" tells our code which menu screen the user is looking at.
# We start in the "MENU" screen.
current_state = "MENU"

# "menu_index" keeps track of which menu option is currently highlighted (0 is the first item).
menu_index = 0

# This list contains all our menu options. A "list" is a collection of items.
menu_items = [
    "1. NET RECON",    # Checks nearby devices on your Wi-Fi.
    "2. HASH CRACK",   # Simulates cracking encrypted passwords.
    "3. SNIFFER",      # Simulates capturing network data.
    "4. IR CLONE",     # Simulates copying TV or AC remote signals.
    "5. GPS TRACKER",  # Simulates connecting to satellite hardware.
    "6. LORA CHAT",    # Simulates sending radio text messages without Wi-Fi.
    "7. SYS INFO"      # Displays details about our hardware.
]

# Shared variables used by background tasks:
scanning = False       # True if a network scan or hash crack is currently running.
scan_results = []      # A list of text lines that will be printed on screen as results.
input_buffer = ""      # Temporary storage for keys the user is typing.
typing_active = False  # True if the user is currently typing a password hash.

# ------------------------------------------------------------------------------
# STEP 5: GPS & LORA HARDWARE EMULATION VARIABLES
# ------------------------------------------------------------------------------
# These variables represent physical add-ons that would plug into the Cardputer.
gps_coords = (40.7128, -74.0060)  # Starts with New York coordinates (Latitude, Longitude).
satellites = 0                    # Starts with 0 connected satellites (locks onto more over time).
gps_log_timer = 0                 # Counts frames so we only save GPS data to a file once in a while.

# This backlog of messages simulates offline radio communication over a mesh network.
lora_messages = ["[MESH] Node_01: Online", "[MESH] Node_02: Signal OK"]
lora_timer = 0                    # Counts frames so a new message arrives every few seconds.

# ------------------------------------------------------------------------------
# STEP 6: WRITING THE FUNCTIONS (The Recipes)
# ------------------------------------------------------------------------------
# A "function" is a block of code with a name. It doesn't run automatically; 
# we call its name when we want it to execute.

# --- Helper Function: Get Local IP Address ---
def get_local_ip():
    """Attempts to figure out your computer's address on your local home network."""
    try:
        # We open a temporary "UDP" (User DAtagram Protocol) socket (like a quick phone call) to Google's public server.
        # This doesn't actually send any data; it just tricks our operating system 
        # into telling us which internal network card we are using.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0] # Grabs the local IP (e.g., "192.168.1.15")
        s.close()
        return ip
    except Exception:
        # If your computer is offline and has no IP, fall back to "localhost" (your own machine).
        return "127.0.0.1"


# --- Task 1: Local Network Recon (Real Wi-Fi Subnet Scanning) ---
def thread_network_recon():
    """Scans your home Wi-Fi subnet to find active devices in the background."""
    global scanning, scan_results
    scanning = True
    scan_results = ["Probing subnet...", "Searching active IPs..."]
    
    local_ip = get_local_ip() # Find out our current IP address.
    parts = local_ip.split('.') # Splits "192.168.1.15" into ["192", "752", "1", "15"]
    
    if len(parts) == 4:
        # Recreate the base subnet (e.g., "192.752.1.")
        subnet = f"{parts[0]}.{parts[1]}.{parts[2]}."
        
        # Scan the first 25 possible device numbers in your household (1 to 25).
        for i in range(1, 26):
            if not scanning: # If the user pressed Escape to exit, stop the loop immediately.
                break
                
            ip = f"{subnet}{i}" # Combine to make a full IP (e.g., "192.752.1.5")
            
            # Create a TCP socket to try to connect to the IP on Port 80 (standard Web browser port).
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1) # Only wait 0.1 seconds for a response. We want to be fast!
            
            # connect_ex tries to connect. If it returns 0, the connection was successful (Host is online).
            res = s.connect_ex((ip, 80))
            if res == 0:
                scan_results.append(f"-> {ip} : Active (HTTP)")
            else:
                # Fallback: If port 80 is closed, check port 135 (common on Windows PCs)
                s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s2.settimeout(0.1)
                res2 = s2.connect_ex((ip, 135))
                if res2 == 0:
                     scan_results.append(f"-> {ip} : Active (NetBIOS)")
                s2.close()
            s.close()
            
    scan_results.append("Scan completed.")
    scanning = False


# --- Task 2: Password Hash Cracker (MD5 Brute Forcer) ---
def thread_hash_crack(target_hash):
    """Attempts to crack a password by guessing every combination of 1 to 4 letters."""
    global scanning, scan_results
    scanning = True
    scan_results = [f"Target: {target_hash[:8]}...", "Cracking: [a-z] up to 4 chars..."]
    
    import string
    import itertools
    chars = string.ascii_lowercase # Generates a string of letters "abcdefghijklmnopqrstuvwxyz"
    found = False
    
    # Loop through guess lengths of 1, 2, 3, and 4 letters.
    for length in range(1, 5):
        if found or not scanning:
            break
            
        scan_results.append(f"Trying length {length}...")
        
        # "itertools.product" automatically generates every possible combination of letters.
        # e.g., "a", "b", "c"... then "aa", "ab", "ac"...
        for guess in itertools.product(chars, repeat=length):
            if not scanning:
                break
                
            guess_str = "".join(guess) # Turn the list of letters into a single word string.
            
            # Convert our guess word into an MD5 hash (encrypted format).
            guess_hash = hashlib.md5(guess_str.encode()).hexdigest()
            
            # Check if our guessed hash matches the target hash.
            if guess_hash == target_hash:
                scan_results.append("SUCCESS!")
                scan_results.append(f"Match found: '{guess_str}'")
                
                # Write our discovery to our "virtual_sd.txt" file so we don't lose it.
                with open("virtual_sd.txt", "a") as f:
                    f.write(f"Cracked {target_hash} -> {guess_str}\n")
                found = True
                break
                
    if not found and scanning:
        scan_results.append("Search finished (No match).")
    scanning = False


# --- Task 3: Packet Sniffer ---
def thread_packet_sniffer():
    """Attempts to capture internet traffic. Falls back to simulated data if run without admin rights."""
    global scanning, scan_results
    scanning = True
    scan_results = ["Initializing Sniffer..."]
    
    try:
        # To monitor raw internet signals on a computer, your OS requires Admin/Root privileges.
        # This line will fail with an error if you didn't run the script as an administrator.
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        s.settimeout(1.0)
        scan_results.append("Sniffing live TCP traffic:")
        
        while scanning:
            try:
                packet, addr = s.recvfrom(65565) # Capture raw packets up to 65,565 bytes.
                scan_results.append(f"TCP {addr[0]} -> Recv {len(packet)}B")
                
                # If our on-screen logs get too long, delete the oldest line to keep it clean.
                if len(scan_results) > 10:
                    scan_results.pop(1)
            except socket.timeout:
                continue
    except OSError:
        # FALLBACK: If we get blocked by lack of admin permissions, simulate realistic packets!
        scan_results.append("Admin/Root block. Running simulated")
        scan_results.append("telemetry:")
        
        while scanning:
            # Wait a random fraction of a second to make packets look like they are arriving live.
            time.sleep(random.uniform(0.3, 0.9))
            
            mock_ips = ["192.168.1.1", "192.168.1.10", "8.8.8.8", "104.244.42.1"]
            src = random.choice(mock_ips) # Grab a random source address.
            dst = get_local_ip()          # Our own address.
            proto = random.choice(["TCP", "UDP", "DNS", "HTTPS"])
            port = random.randint(80, 8080)
            
            scan_results.append(f"[{proto}] {src} -> {dst}:{port}")
            if len(scan_results) > 9:
                scan_results.pop(2) # Keep the list short.
                
    scanning = False


# --- Helper Function: Draw Text on the Screen ---
def draw_text(surface, text, x, y, color=COLOR_TEXT):
    """A quick tool to turn raw text strings into colored pixels at (x, y) coordinates."""
    # "render" turns text into an image. "blit" pastes that image onto our surface.
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))


# ------------------------------------------------------------------------------
# STEP 7: THE MAIN PROGRAM LOOP (The Heartbeat)
# ------------------------------------------------------------------------------
# An interactive app runs inside a "while loop". This block of code runs 
# repeatedly (30 times a second) until the user decides to close the window.

running = True
captured_ir_code = "" # Stores our simulated copied TV remote signal.

while running:
    # --- PART A: LISTENING FOR INPUTS (Keyboard & Mouse) ---
    # Pygame keeps a list of "events" (like clicking the close button or typing keys).
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # If you clicked the "X" button on the window, stop the loop and exit.
            scanning = False
            running = False
            
        elif event.type == pygame.KEYDOWN:
            # If the user presses the "ESCAPE" key, cancel background tasks and go back to the menu.
            if event.key == pygame.K_ESCAPE:
                scanning = False
                current_state = "MENU"
                
            elif current_state == "MENU":
                # Navigating the menu list using Up and Down arrows:
                if event.key == pygame.K_UP:
                    # Move selection up (wrap around to the bottom if we go past 0).
                    menu_index = (menu_index - 1) % len(menu_items)
                elif event.key == pygame.K_DOWN:
                    # Move selection down (wrap around to the top if we go past the end).
                    menu_index = (menu_index + 1) % len(menu_items)
                elif event.key == pygame.K_RETURN:
                    # If the user presses "ENTER" on a menu option, switch to that module.
                    if menu_index == 0:
                        current_state = "NETSCAN"
                        scan_results = []
                        # "threading.Thread" starts our function in a background thread 
                        # so the screen does not freeze while scanning the network.
                        threading.Thread(target=thread_network_recon, daemon=True).start()
                    elif menu_index == 1:
                        current_state = "HASHCRACK"
                        input_buffer = "81dc9bdb52d04dc20036dbd8313ed055"  # Pre-fill with MD5 hash for "1234"
                        typing_active = True
                        scan_results = []
                    elif menu_index == 2:
                        current_state = "SNIFFER"
                        scan_results = []
                        threading.Thread(target=thread_packet_sniffer, daemon=True).start()
                    elif menu_index == 3:
                        current_state = "IRCLONE"
                        captured_ir_code = "" # Reset IR capture.
                    elif menu_index == 4:
                        current_state = "GPSTRACKER"
                        satellites = 0 # Start searching for satellites.
                        gps_log_timer = 0
                    elif menu_index == 5:
                        current_state = "LORACHAT"
                        lora_timer = 0
                    elif menu_index == 6:
                        current_state = "SYSINFO"
                        
            elif current_state == "HASHCRACK" and typing_active:
                # If the user is on the password screen and typing:
                if event.key == pygame.K_RETURN:
                    typing_active = False
                    # Start cracking the typed hash in the background.
                    threading.Thread(target=thread_hash_crack, args=(input_buffer,), daemon=True).start()
                elif event.key == pygame.K_BACKSPACE:
                    input_buffer = input_buffer[:-1] # Delete the last letter typed.
                else:
                    # Only accept hexadecimal letters (0-9 and a-f) up to 32 characters long.
                    if len(input_buffer) < 32 and event.unicode in "0123456789abcdefABCDEF":
                        input_buffer += event.unicode.lower()

            elif current_state == "IRCLONE":
                # If they are on the IR Clone screen and press any key:
                if event.key != pygame.K_ESCAPE and not captured_ir_code:
                    # Generate a random 8-character code representing an infrared signal.
                    raw_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8].upper()
                    captured_ir_code = f"NEC 0x{raw_hash}"
                    # Save the code to our virtual SD card.
                    with open("virtual_sd.txt", "a") as f:
                        f.write(f"IR Captured: {captured_ir_code}\n")

    # --- PART B: BACKGROUND PROCESS CALCULATIONS ---
    # These blocks update our simulated hardware calculations in real-time.
    
    if current_state == "GPSTRACKER":
        # Slowly find satellites over time (approx 2% chance per frame to find a satellite).
        if satellites < 8 and random.random() < 0.02:
            satellites += 1
        
        # Drift GPS coordinates slightly to show that the tracking marker is moving.
        if random.random() < 0.05:
            gps_coords = (gps_coords[0] + random.uniform(-0.00005, 0.00005), 
                          gps_coords[1] + random.uniform(-0.00005, 0.00005))
            
        # Log active GPS coordinates to "virtual_sd.txt" every 5 seconds (150 frames).
        gps_log_timer += 1
        if gps_log_timer >= 150:
            gps_log_timer = 0
            if satellites >= 3: # Needs at least 3 satellites for a valid location triangulation.
                with open("virtual_sd.txt", "a") as f:
                    f.write(f"GPS Tracked: Lat {gps_coords[0]:.6f}, Lon {gps_coords[1]:.6f} ({satellites} Sats)\n")

    elif current_state == "LORACHAT":
        # Simulate receiving offline text message packets from other nodes every 4 seconds (120 frames).
        lora_timer += 1
        if lora_timer >= 120:
            lora_timer = 0
            sender = random.choice(["Node_01", "Node_02", "Gateway_S3", "Router_Alpha"])
            text = random.choice(["Ping acknowledged", "Battery level: 78%", "Mesh relay online", "Ack from Gateway", "SNR: 8dBm"])
            lora_messages.append(f"[{sender}] {text}")
            if len(lora_messages) > 8:
                lora_messages.pop(0) # Keep on-screen logs short.

    # --- PART C: RENDERING (Drawing the Graphics) ---
    # 1. Fill the background of our tiny virtual drawing board with dark green.
    virtual_screen.fill(COLOR_BG)
    
    # 2. Draw the Title Bar at the top of the screen (height of 12 pixels).
    pygame.draw.rect(virtual_screen, COLOR_ACCENT, (0, 0, V_WIDTH, 12))
    draw_text(virtual_screen, f"PORTHACK-S3  v1.0.0", 4, 1, COLOR_WHITE)
    draw_text(virtual_screen, "[ESC] BACK", 185, 1, COLOR_WHITE)
    
    # 3. Draw the active screen depending on "current_state":
    
    if current_state == "MENU":
        draw_text(virtual_screen, "=== CHOOSE SYSTEM MODULE ===", 10, 18, COLOR_ACCENT)
        for i, item in enumerate(menu_items):
            # Highlight the currently selected menu index in white; draw others in green.
            color = COLOR_WHITE if i == menu_index else COLOR_TEXT
            prefix = " > " if i == menu_index else "   "
            draw_text(virtual_screen, f"{prefix}{item}", 10, 32 + (i * 12), color)
            
        draw_text(virtual_screen, "Use UP/DOWN keys & PRESS [ENTER]", 10, 118, COLOR_ACCENT)
        
    elif current_state == "NETSCAN":
        draw_text(virtual_screen, "MODULE: LOCAL IP SCANNER", 10, 16, COLOR_WHITE)
        y_offset = 32
        for line in scan_results[-8:]:  # Display only the 8 most recent lines of results.
            draw_text(virtual_screen, line, 10, y_offset)
            y_offset += 11
            
    elif current_state == "HASHCRACK":
        draw_text(virtual_screen, "MODULE: MD5 CRACKER TOOL", 10, 16, COLOR_WHITE)
        if typing_active:
            draw_text(virtual_screen, "INPUT TARGET MD5 HASH:", 10, 32, COLOR_ACCENT)
            # Draw an input text box block.
            pygame.draw.rect(virtual_screen, (20, 40, 20), (10, 44, 220, 14))
            # Blinking cursor effect using a timer.
            cursor = "|" if time.time() % 1 > 0.5 else ""
            draw_text(virtual_screen, input_buffer + cursor, 12, 46, COLOR_WHITE)
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

    elif current_state == "GPSTRACKER":
        draw_text(virtual_screen, "MODULE: GPS SATELLITE HAT", 10, 16, COLOR_WHITE)
        if satellites < 3:
            draw_text(virtual_screen, "ACQUIRING SATELLITE FIX...", 10, 45, COLOR_RED)
            # Create a blinking radar sweep notification.
            if (pygame.time.get_ticks() // 250) % 2 == 0:
                draw_text(virtual_screen, ">>> TRACE ACTIVE <<<", 10, 70, COLOR_ACCENT)
            draw_text(virtual_screen, f"Sats Connected: {satellites}/3 (Min)", 10, 95, COLOR_TEXT)
        else:
            draw_text(virtual_screen, f"STATUS: LOCKED ({satellites} Sats)", 10, 32, COLOR_TEXT)
            draw_text(virtual_screen, f"LAT: {gps_coords[0]:.6f}", 10, 47, COLOR_WHITE)
            draw_text(virtual_screen, f"LON: {gps_coords[1]:.6f}", 10, 62, COLOR_WHITE)
            draw_text(virtual_screen, f"ALT: 42.5 meters (MSL)", 10, 77, COLOR_TEXT)
            draw_text(virtual_screen, "Logging trajectory to SD Card", 10, 100, COLOR_ACCENT)

    elif current_state == "LORACHAT":
        draw_text(virtual_screen, "MODULE: LORA MESH NET (433MHz)", 10, 16, COLOR_WHITE)
        y_offset = 30
        for msg in lora_messages[-8:]:
            draw_text(virtual_screen, msg, 10, y_offset)
            y_offset += 11
            
    elif current_state == "SYSINFO":
        draw_text(virtual_screen, "MODULE: HARDWARE DIAGNOSTIC", 10, 16, COLOR_WHITE)
        draw_text(virtual_screen, f"CPU Emulation: ESP32-S3 @ 240MHz", 10, 32, COLOR_TEXT)
        draw_text(virtual_screen, f"Local IP Address: {get_local_ip()}", 10, 47, COLOR_TEXT)
        draw_text(virtual_screen, f"Virtual Flash Storage: 4.0 MB", 10, 62, COLOR_TEXT)
        draw_text(virtual_screen, f"Memory Allocation: < 512 KB RAM", 10, 77, COLOR_TEXT)
        draw_text(virtual_screen, f"OS Target: FreeRTOS / ESP-IDF", 10, 92, COLOR_TEXT)
        draw_text(virtual_screen, f"SD Card: virtual_sd.txt (ACTIVE)", 10, 107, COLOR_ACCENT)

    # 4. STRETCH AND DISPLAY GRAPHICS
    # Take our tiny 240x135 drawing board, stretch it using Pygame's scaling tool,
    # and paste it onto the active 960x540 window that the user is looking at.
    scaled_surface = pygame.transform.scale(virtual_screen, (WINDOW_WIDTH, WINDOW_HEIGHT))
    screen.blit(scaled_surface, (0, 0))
    pygame.display.flip() # Refresh the computer screen with our new frame.
    
    # 5. LIMIT RUNTIME SPEED
    # Pause for a split millisecond so the loop runs at exactly 30 frames per second.
    # This keeps your CPU cool so it doesn't try to run millions of times a second.
    clock.tick(30)

# --- CLEANUP (Shutdown) ---
# If the main while loop stops, safely close Pygame and close the window.
pygame.quit()
sys.exit()
# This program is for Portputer YSWS by Hackclub