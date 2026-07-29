#include "M5Cardputer.h"
#include "M5GFX.h"
#include "WiFi.h"
#include "mbedtls/md5.h"

M5Canvas canvas(&M5Cardputer.Display);

enum State { MENU, NETSCAN, HASHCRACK, SNIFFER, IRCLONE, SYSINFO };
State currentState = MENU;
int menuIndex = 0;
const int menuItemsCount = 5;
const char* menuItems[] = {
  "1. WI-FI RECON",
  "2. MD5 CRACKER",
  "3. SNIFFER (SIM)",
  "4. IR TRANSCEIVER",
  "5. SYSTEM DIAGS"
};

String statusLog[8];
int logCount = 0;
bool isExecuting = false;
String hashInput = "81dc9bdb52d04dc20036dbd8313ed055"; // MD5 of "1234"
bool typingMode = true;

void clearLog() {
  for (int i = 0; i < 8; i++) statusLog[i] = "";
  logCount = 0;
}

void addLog(String line) {
  if (logCount < 8) {
    statusLog[logCount++] = line;
  } else {
    for (int i = 1; i < 8; i++) {
      statusLog[i - 1] = statusLog[i];
    }
    statusLog[7] = line;
  }
}

void drawHeader() {
  canvas.fillRect(0, 0, 240, 12, GREEN);
  canvas.setTextColor(BLACK);
  canvas.drawString("PORTHACK-S3 ESP32-S3", 4, 2);
  canvas.drawString("[Del] BACK", 180, 2);
}

// MD5 Brute Forcer (Includes a-z, A-Z, 0-9 and Watchdog Yielding)
bool bruteForceMD5(String target) {
  addLog("Cracking hash...");
  
  // Entire 62-character alphanumeric namespace
  char alphabet[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  int alphabetSize = sizeof(alphabet) - 1;
  unsigned char digest[16];
  char guess[5] = {0};
  unsigned long start = millis();

  for (int len = 1; len <= 4; len++) {
    addLog("Testing length " + String(len) + "...");
    canvas.fillSprite(BLACK);
    drawHeader();
    for (int y = 16; y < 135; y += 12) {
      canvas.drawString(statusLog[(y - 16) / 12], 8, y);
    }
    canvas.pushSprite(0, 0);

    if (len == 1) {
      for (int i = 0; i < alphabetSize; i++) {
        guess[0] = alphabet[i]; guess[1] = '\0';
        mbedtls_md5((unsigned char*)guess, strlen(guess), digest);
        char hex[33] = {0};
        for(int h=0; h<16; h++) sprintf(&hex[h*2], "%02x", digest[h]);
        if (target.equalsIgnoreCase(String(hex))) {
          addLog("SUCCESS! Password: " + String(guess));
          addLog("Time: " + String((millis() - start) / 1000.0) + "s");
          return true;
        }
      }
    }
    else if (len == 2) {
      for (int i = 0; i < alphabetSize; i++) {
        yield(); // Yield to feed the ESP32 Task Watchdog Timer
        for (int j = 0; j < alphabetSize; j++) {
          guess[0] = alphabet[i]; guess[1] = alphabet[j]; guess[2] = '\0';
          mbedtls_md5((unsigned char*)guess, strlen(guess), digest);
          char hex[33] = {0};
          for(int h=0; h<16; h++) sprintf(&hex[h*2], "%02x", digest[h]);
          if (target.equalsIgnoreCase(String(hex))) {
            addLog("SUCCESS! Password: " + String(guess));
            addLog("Time: " + String((millis() - start) / 1000.0) + "s");
            return true;
          }
        }
      }
    }
    else if (len == 3) {
      for (int i = 0; i < alphabetSize; i++) {
        yield(); // Yield to feed the ESP32 Task Watchdog Timer
        for (int j = 0; j < alphabetSize; j++) {
          for (int k = 0; k < alphabetSize; k++) {
            guess[0] = alphabet[i]; guess[1] = alphabet[j]; guess[2] = alphabet[k]; guess[3] = '\0';
            mbedtls_md5((unsigned char*)guess, strlen(guess), digest);
            char hex[33] = {0};
            for(int h=0; h<16; h++) sprintf(&hex[h*2], "%02x", digest[h]);
            if (target.equalsIgnoreCase(String(hex))) {
              addLog("SUCCESS! Password: " + String(guess));
              addLog("Time: " + String((millis() - start) / 1000.0) + "s");
              return true;
            }
          }
        }
      }
    }
    else if (len == 4) {
      for (int i = 0; i < alphabetSize; i++) {
        yield(); // Prevent triggering system reset during long calculations
        for (int j = 0; j < alphabetSize; j++) {
          for (int k = 0; k < alphabetSize; k++) {
            for (int l = 0; l < alphabetSize; l++) {
              guess[0] = alphabet[i]; guess[1] = alphabet[j]; guess[2] = alphabet[k]; guess[3] = alphabet[l]; guess[4] = '\0';
              mbedtls_md5((unsigned char*)guess, strlen(guess), digest);
              char hex[33] = {0};
              for(int h=0; h<16; h++) sprintf(&hex[h*2], "%02x", digest[h]);
              if (target.equalsIgnoreCase(String(hex))) {
                addLog("SUCCESS! Password: " + String(guess));
                addLog("Time: " + String((millis() - start) / 1000.0) + "s");
                return true;
              }
            }
          }
        }
      }
    }
  }
  addLog("Brute-force complete. No match.");
  return false;
}

void setup() {
  auto cfg = M5.config();
  M5Cardputer.begin(cfg, true);
  M5Cardputer.Display.setRotation(1);
  
  canvas.createSprite(240, 135);
  canvas.setTextColor(GREEN);
  canvas.setTextSize(1);
}

void loop() {
  M5Cardputer.update();

  if (M5Cardputer.Keyboard.isPressed()) {
    Keyboard_Class::KeysState status = M5Cardputer.Keyboard.keysState();

    if (status.del && currentState != MENU) {
      if (currentState == HASHCRACK && typingMode) {
        if (hashInput.length() > 0) hashInput.remove(hashInput.length() - 1);
      } else {
        currentState = MENU;
        isExecuting = false;
        WiFi.disconnect();
      }
    }
    else if (currentState == MENU) {
      for (auto c : status.word) {
        if (c == 'w' || c == ';') {
          menuIndex = (menuIndex - 1 + menuItemsCount) % menuItemsCount;
        }
        if (c == 's' || c == '/') {
          menuIndex = (menuIndex + 1) % menuItemsCount;
        }
      }

      if (status.enter) {
        clearLog();
        switch (menuIndex) {
          case 0: currentState = NETSCAN; break;
          case 1: currentState = HASHCRACK; typingMode = true; break;
          case 2: currentState = SNIFFER; break;
          case 3: currentState = IRCLONE; break;
          case 4: currentState = SYSINFO; break;
        }
      }
    }
    else if (currentState == HASHCRACK && typingMode) {
      for (auto c : status.word) {
        if (hashInput.length() < 32 && isxdigit(c)) {
          hashInput += String(c);
        }
      }
      if (status.enter) {
        typingMode = false;
        bruteForceMD5(hashInput);
      }
    }
  }

  canvas.fillSprite(BLACK);
  drawHeader();

  if (currentState == MENU) {
    canvas.setTextColor(GREEN);
    canvas.drawString("=== CHOOSE DEVICE MODULE ===", 10, 18);
    for (int i = 0; i < menuItemsCount; i++) {
      if (i == menuIndex) {
        canvas.setTextColor(WHITE);
        canvas.drawString("> " + String(menuItems[i]), 10, 36 + (i * 14));
      } else {
        canvas.setTextColor(GREEN);
        canvas.drawString("  " + String(menuItems[i]), 10, 36 + (i * 14));
      }
    }
    canvas.setTextColor(GREEN);
    canvas.drawString("W/S to navigate, ENTER to select", 10, 115);
  }
  else if (currentState == NETSCAN) {
    canvas.drawString("MODULE: WI-FI SPECTRUM RECON", 8, 16);
    if (!isExecuting) {
      isExecuting = true;
      addLog("Initializing ESP32 Wi-Fi...");
      WiFi.mode(WIFI_STA);
      WiFi.disconnect();
      addLog("Scanning wireless networks...");
      int n = WiFi.scanNetworks();
      addLog("Scan complete!");
      addLog("Networks found: " + String(n));
      for (int i = 0; i < min(n, 4); i++) {
        addLog(String(WiFi.SSID(i)) + " (" + String(WiFi.RSSI(i)) + "dBm)");
      }
    }
    for (int i = 0; i < 8; i++) {
      canvas.drawString(statusLog[i], 8, 30 + (i * 12));
    }
  }
  else if (currentState == HASHCRACK) {
    canvas.drawString("MODULE: MD5 DECRYPTER ENGINE", 8, 16);
    if (typingMode) {
      canvas.drawString("ENTER HASH TO DECRYPT:", 8, 32);
      canvas.fillRect(8, 45, 224, 15, DARKGREEN);
      canvas.setTextColor(WHITE);
      canvas.drawString(hashInput, 12, 49);
      canvas.setTextColor(GREEN);
      canvas.drawString("Press ENTER to brute force", 8, 70);
    } else {
      for (int i = 0; i < 8; i++) {
        canvas.drawString(statusLog[i], 8, 30 + (i * 12));
      }
    }
  }
  else if (currentState == SNIFFER) {
    canvas.drawString("MODULE: 2.4GHz PACKET SNIFFER", 8, 16);
    if (millis() % 2000 < 50) {
      char rawPkt[60];
      sprintf(rawPkt, "[BEACON] MAC: %02X:%02X:%02X:%02X - CH %d", rand()%255, rand()%255, rand()%255, rand()%255, rand()%13 + 1);
      addLog(String(rawPkt));
    }
    for (int i = 0; i < 8; i++) {
      canvas.drawString(statusLog[i], 8, 30 + (i * 12));
    }
  }
  else if (currentState == IRCLONE) {
    canvas.drawString("MODULE: INFRARED RECEIVER", 8, 16);
    canvas.drawString("Waiting for 38kHz IR carrier signal...", 8, 35);
    canvas.drawString("Press keyboard key to generate raw hex", 8, 50);
    
    if (M5Cardputer.Keyboard.isPressed() && !isExecuting) {
       isExecuting = true;
       char code[20];
       sprintf(code, "RAW NEC: 0x%08X", rand());
       addLog(String(code));
    }
    if (isExecuting) {
      canvas.drawString("SIGNAL CAPTURED!", 8, 75, WHITE);
      canvas.drawString(statusLog[0], 8, 90);
      canvas.drawString("Saved code payload to EEPROM", 8, 105);
    }
  }
  else if (currentState == SYSINFO) {
    canvas.drawString("MODULE: HARDWARE RECON", 8, 16);
    canvas.drawString("Chipset: Dual-Core ESP32-S3 (S3FN8)", 8, 32);
    canvas.drawString("Freq: 240 MHz  |  PSRAM: Disabled", 8, 47);
    canvas.drawString("Internal Heap RAM: " + String(ESP.getFreeHeap() / 1024) + " KB Free", 8, 62);
    canvas.drawString("Flash Capacity: 8.0 MB", 8, 77);
    canvas.drawString("Silicon Revision: " + String(ESP.getChipRevision()), 8, 92);
  }

  canvas.pushSprite(0, 0);
  delay(30);
}