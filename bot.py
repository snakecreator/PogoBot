#!/usr/bin/env python3
"""
Pokemon GO Auto Battle Bot
Automatycznie walczy z Candelą w Great League z teamem [dowolny 1 pokemon, 
vaporeon, dowolny 3 pokemon]. Zmienia na 2 slot na początku walki

SPOSÓB URUCHOMIENIA:
    python3 bot.py                    # walcz w nieskończoność
    python3 bot.py --walki 50         # zatrzymaj po 50 walkach
    python3 bot.py --minuty 120       # zatrzymaj po 2 godzinach
"""

import subprocess
import cv2
import numpy as np
import time
import argparse
import sys
import json
import os
from datetime import datetime

# ── Konfiguracja ──────────────────────────────────────────────────────────────

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
SCREENSHOT_PATH = os.path.join(os.path.dirname(__file__), "pogo_screen.png")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)

# Maksymalny czas oczekiwania na element interfejsu (sekundy)
TIMEOUT = CONFIG["timeout_seconds"]

# Odstęp czasowy między pętlowymi kliknięciami ataku (sekundy)
CLICK_INTERVAL = CONFIG["click_interval_seconds"]

# Zakładany maksymalny czas trwania jednej walki (sekundy)
CZAS_WALKI = CONFIG["battle_duration_seconds"]

# Próg dokładności dopasowania obrazu w OpenCV (0.0 - 1.0)
THRESHOLD = CONFIG["opencv_threshold"]

# Względne pozycje kliknięć na ekranie (X%, Y%)
RATIO_ATTACK = tuple(CONFIG["ratio_attack"])          # Środek-dół (atak i tarcza)
RATIO_SWITCH_SLOT2 = tuple(CONFIG["ratio_switch_slot2"])  # Prawa strona (zmiana na 2. slot)

# Zmienne globalne na wymiary ekranu (wyliczane dynamicznie przy starcie bota)
SCREEN_W = 0
SCREEN_H = 0

def pobierz_rozdzielczosc():
    """Pobiera szerokość i wysokość ekranu podłączonego telefonu przez ADB."""
    res = subprocess.run(
        ["adb", "shell", "wm", "size"], capture_output=True, text=True
    )
    size_str = res.stdout.split(":")[-1].strip()
    width, height = map(int, size_str.split("x"))
    return width, height


# ── ADB ───────────────────────────────────────────────────────────────────────

def screenshot():
    """Pobiera screenshot z telefonu."""
    subprocess.run(
        ["adb", "exec-out", "screencap", "-p"],
        stdout=open(SCREENSHOT_PATH, "wb"),
        stderr=subprocess.DEVNULL,
    )
    return cv2.imread(SCREENSHOT_PATH)


def tap(x, y):
    """Klika w punkt (x, y) na ekranie telefonu."""
    subprocess.run(
        ["adb", "shell", "input", "tap", str(x), str(y)],
        stderr=subprocess.DEVNULL,
    )

def tap_ratio(ratio_x, ratio_y):
    """Klika w punkt przeliczony z proporcji na rzeczywiste piksele."""
    x = int(SCREEN_W * ratio_x)
    y = int(SCREEN_H * ratio_y)
    tap(x, y)

# ── OpenCV ────────────────────────────────────────────────────────────────────

def znajdz(screen, template_name):
    """
    Szuka template na ekranie.
    Zwraca (score, x, y) środka znalezionego elementu.
    """
    path = os.path.join(TEMPLATES_DIR, template_name)
    template = cv2.imread(path)
    if template is None:
        raise FileNotFoundError(f"Nie znaleziono templateki: {path}")

    # Upewnij się że oba obrazy mają ten sam format
    if screen.shape[2] != template.shape[2]:
        template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
    screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    h, w = template.shape[:2]
    cx = max_loc[0] + w // 2
    cy = max_loc[1] + h // 2
    return max_val, cx, cy


def czekaj_na(template_name, timeout=TIMEOUT, threshold=THRESHOLD):
    """
    Czeka aż template pojawi się na ekranie.
    Zwraca (x, y) lub None jeśli timeout.
    """
    log(f"  Czekam na: {template_name}")
    start = time.time()
    while time.time() - start < timeout:
        screen = screenshot()
        val, cx, cy = znajdz(screen, template_name)
        if val >= threshold:
            log(f"  Znaleziono {template_name} (score={val:.2f}) @ ({cx}, {cy})")
            return cx, cy
        time.sleep(0.5)
    log(f"  TIMEOUT: nie znaleziono {template_name} po {timeout}s")
    return None


def czekaj_i_kliknij(template_name, timeout=TIMEOUT, delay_po=0.5):
    """
    Czeka na element i klika go. Zwraca True jeśli sukces.
    """
    pos = czekaj_na(template_name, timeout)
    if pos is None:
        return False
    time.sleep(0.1)  # chwila przed kliknięciem
    tap(*pos)
    time.sleep(delay_po)
    return True


# ── Logi ─────────────────────────────────────────────────────────────────

def log(msg):
    teraz = datetime.now().strftime("%H:%M:%S")
    print(f"[{teraz}] {msg}")


# ── Główna logika ─────────────────────────────────────────────────────────────

def jedna_walka(numer):
    log(f"═══ Walka #{numer} ═══")

    # 1. Kliknij ikonkę Candeli
    log("Krok 1: Candela")
    if not czekaj_i_kliknij("candela_icon.png", delay_po=1.0):
        log("BŁĄD: Nie znaleziono Candeli — czy jesteś na ekranie startowym?")
        return False

    # 2. Kliknij BATTLE
    log("Krok 2: BATTLE")
    if not czekaj_i_kliknij("battle_btn.png", delay_po=1.0):
        log("BŁĄD: Nie znaleziono przycisku BATTLE")
        return False

    # 3. Kliknij Great League
    log("Krok 3: Great League")
    if not czekaj_i_kliknij("great_league.png", delay_po=1.0):
        log("BŁĄD: Nie znaleziono Great League")
        return False

    # 4. Kliknij USE THIS PARTY
    log("Krok 4: USE THIS PARTY")
    if not czekaj_i_kliknij("use_this_party.png", delay_po=2.0):
        log("BŁĄD: Nie znaleziono USE THIS PARTY")
        return False

    # 5. Zmiana na Vaporeon (klikaj przez 3s w slot 2)
    log("Krok 5: Zmiana na Vaporeon")
    time.sleep(5)  # poczekaj 5s po USE THIS PARTY
    koniec_swap = time.time() + 3
    while time.time() < koniec_swap:
        tap_ratio(*RATIO_SWITCH_SLOT2)
        time.sleep(0.04)

    # 6. Klikaj przez czas walki
    log(f"Krok 6: Klikanie przez {CZAS_WALKI}s")
    koniec_walki = time.time() + CZAS_WALKI
    szukaj_od = time.time() + 50  # zacznij szukać YOU WIN po 50s

    while time.time() < koniec_walki:
        tap_ratio(*RATIO_ATTACK)
        if time.time() > szukaj_od:
            screen = screenshot()
            val, cx, cy = znajdz(screen, "you_win.png")
            if val >= THRESHOLD:
                log("YOU WIN wykryto!")
                break
        time.sleep(CLICK_INTERVAL)

    # 7. Kliknij checkmark 
    log("Krok 7: Potwierdzenie YOU WIN")
    if not czekaj_i_kliknij("checkmark.png", timeout=15, delay_po=2.0):
        log("BŁĄD: Nie znaleziono checkmark")
        return False

    # 8. Poczekaj na powrót do ekranu startowego
    log("Krok 8: Czekam na ekran startowy")
    if czekaj_na("training.png", timeout=10) is None:
        log("OSTRZEŻENIE: Ekran startowy nie pojawił się, kontynuuję mimo to")

    log(f"Walka #{numer} zakończona sukcesem!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Pokemon GO Auto Battle Bot")
    parser.add_argument("--walki", type=int, default=0,
                        help="Liczba walk (0 = nieskończoność)")
    parser.add_argument("--minuty", type=int, default=0,
                        help="Czas działania w minutach (0 = nieskończoność)")
    args = parser.parse_args()

    # Sprawdź połączenie ADB
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    if "device" not in result.stdout:
        print("BŁĄD: Telefon nie jest podłączony lub ADB nie działa.")
        print("Uruchom: adb devices")
        sys.exit(1)

    global SCREEN_W, SCREEN_H
    SCREEN_W, SCREEN_H = pobierz_rozdzielczosc()
    log(f"Wykryto rozdzielczość ekranu: {SCREEN_W}x{SCREEN_H}")

    log("Bot uruchomiony!")
    if args.walki:
        log(f"Cel: {args.walki} walk")
    if args.minuty:
        log(f"Cel: {args.minuty} minut")
    log("Przejdź do ekranu Battle w Pokemon GO. Masz 5 sekund...")
    time.sleep(5)

    walka_nr = 0
    bledy = 0
    czas_start = time.time()
    czas_limit = args.minuty * 60 if args.minuty else 0

    try:
        while True:
            # Sprawdź limity
            if args.walki and walka_nr >= args.walki:
                log(f"Osiągnięto limit {args.walki} walk. Kończę.")
                break
            if czas_limit and (time.time() - czas_start) >= czas_limit:
                log(f"Osiągnięto limit {args.minuty} minut. Kończę.")
                break

            walka_nr += 1
            sukces = jedna_walka(walka_nr)

            if not sukces:
                bledy += 1
                log(f"Błąd w walce #{walka_nr}. Błędów łącznie: {bledy}")
                if bledy >= 3:
                    log("3 błędy z rzędu — zatrzymuję bota.")
                    break
                log("Czekam 10s i próbuję ponownie...")
                time.sleep(10)
            else:
                bledy = 0  # reset licznika błędów po sukcesie
                time.sleep(1)  # krótka pauza między walkami

    except KeyboardInterrupt:
        log("Zatrzymano przez użytkownika (Ctrl+C)")

    # Podsumowanie
    czas_total = int(time.time() - czas_start)
    log(f"═══ Podsumowanie ═══")
    log(f"Walki: {walka_nr}")
    log(f"Czas: {czas_total // 60}m {czas_total % 60}s")

    # Powiadomienie Ubuntu
    subprocess.run([
        "notify-send",
        "Pokemon GO Bot",
        f"Zakończono! Walki: {walka_nr}, Czas: {czas_total // 60}m"
    ], stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
