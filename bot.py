#!/usr/bin/env python3
"""
Pokémon GO Auto Battle Bot
Automatically battles Candela in the Great League using the team [any 1st Pokémon, Vaporeon, any 3rd Pokémon]. 
Switches to the 2nd slot at the start of the battle.

HOW TO RUN:
python3 bot.py                     # battle indefinitely
python3 bot.py --fights 50         # stop after 50 battles
python3 bot.py --minutes 120       # stop after 2 hours
python3 bot.py --help              # shows usage 
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

# ── Configuration ─────────────────────────────────────────────────────────────

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
SCREENSHOT_PATH = os.path.join(os.path.dirname(__file__), "pogo_screen.png")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)

# Maximum wait time for an interface element (seconds)
TIMEOUT = CONFIG["timeout_seconds"]

# Time interval between repeated attack taps (seconds)
CLICK_INTERVAL = CONFIG["click_interval_seconds"]

# Assumed maximum duration of a single battle (seconds)
BATTLE_DURATION = CONFIG["battle_duration_seconds"]

# OpenCV template matching confidence threshold (0.0 - 1.0)
THRESHOLD = CONFIG["opencv_threshold"]

# Relative tap coordinates on the screen (X%, Y%)
RATIO_ATTACK = tuple(CONFIG["ratio_attack"])               # Bottom-center (attack and shield)
RATIO_SWITCH_SLOT2 = tuple(CONFIG["ratio_switch_slot2"])   # Right side (switch to 2nd slot)

# Global variables for screen dimensions (calculated dynamically at bot startup)
SCREEN_W = 0
SCREEN_H = 0

def get_screen_resolution():
    """Retrieves screen width and height of the connected phone via ADB."""
    res = subprocess.run(
        ["adb", "shell", "wm", "size"], capture_output=True, text=True
    )
    size_str = res.stdout.split(":")[-1].strip()
    width, height = map(int, size_str.split("x"))
    return width, height

# ── ADB ───────────────────────────────────────────────────────────────────────
def screenshot():
    """Captures a screenshot from the phone."""
    subprocess.run(
        ["adb", "exec-out", "screencap", "-p"],
        stdout=open(SCREENSHOT_PATH, "wb"),
        stderr=subprocess.DEVNULL,
    )
    return cv2.imread(SCREENSHOT_PATH)

def tap(x, y):
    """Taps on point (x, y) on the phone screen."""
    subprocess.run(
        ["adb", "shell", "input", "tap", str(x), str(y)],
        stderr=subprocess.DEVNULL,
    )

def tap_ratio(ratio_x, ratio_y):
    """Taps on a point calculated from relative coordinates to actual pixels."""
    x = int(SCREEN_W * ratio_x)
    y = int(SCREEN_H * ratio_y)
    tap(x, y)

# ── OpenCV ────────────────────────────────────────────────────────────────────
def find_template(screen, template_name):
    """
    Searches for a template image on screen.
    Returns (score, x, y) of the center of the found element.
    """
    path = os.path.join(TEMPLATES_DIR, template_name)
    template = cv2.imread(path)
    if template is None:
        raise FileNotFoundError(f"Template image not found: {path}")

    # Ensure both images share the same color space format
    if screen.shape[2] != template.shape[2]:
        template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
    screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    h, w = template.shape[:2]
    cx = max_loc[0] + w // 2
    cy = max_loc[1] + h // 2
    return max_val, cx, cy


def wait_for(template_name, timeout=TIMEOUT, threshold=THRESHOLD):
    """
    Waits for a template image to appear on screen.
    Returns (x, y) coordinates or None if timed out.
    """
    log(f"  Waiting for: {template_name}")
    start = time.time()
    while time.time() - start < timeout:
        screen = screenshot()
        val, cx, cy = find_template(screen, template_name)
        if val >= threshold:
            log(f"  Found {template_name} (score={val:.2f}) @ ({cx}, {cy})")
            return cx, cy
        time.sleep(0.5)
    log(f"  TIMEOUT: {template_name} not found after {timeout}s")
    return None


def wait_and_tap(template_name, timeout=TIMEOUT, delay_after=0.5):
    """
    Waits for an element and taps it. Returns True if successful.
    """
    pos = wait_for(template_name, timeout)
    if pos is None:
        return False
    time.sleep(0.1)  # brief pause before tapping
    tap(*pos)
    time.sleep(delay_after)
    return True


# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")


# ── Main Logic ────────────────────────────────────────────────────────────────
def run_single_battle(number):
    log(f"═══ Battle #{number} ═══")

    # 1. Tap Candela icon
    log("Step 1: Candela")
    if not wait_and_tap("candela_icon.png", delay_after=1.0):
        log("ERROR: Candela not found. Are you on the starting screen?")
        return False

    # 2. Tap BATTLE button
    log("Step 2: BATTLE")
    if not wait_and_tap("battle_btn.png", delay_after=1.0):
        log("ERROR: BATTLE button not found")
        return False

    # 3. Tap Great League
    log("Step 3: Great League")
    if not wait_and_tap("great_league.png", delay_after=1.0):
        log("ERROR: Great League option not found")
        return False

    # 4. Tap USE THIS PARTY
    log("Step 4: USE THIS PARTY")
    if not wait_and_tap("use_this_party.png", delay_after=2.0):
        log("ERROR: USE THIS PARTY button not found")
        return False

    # 5. Switch to Vaporeon (tap slot 2 repeatedly for 3s)
    log("Step 5: Switching to Vaporeon")
    time.sleep(5)  # wait 5s after clicking USE THIS PARTY
    swap_end_time = time.time() + 3
    while time.time() < swap_end_time:
        tap_ratio(*RATIO_SWITCH_SLOT2)
        time.sleep(0.04)

    # 6. Tap repeatedly for the duration of the battle
    log(f"Step 6: Tapping for {BATTLE_DURATION}s")
    battle_end_time = time.time() + BATTLE_DURATION
    start_searching_win = time.time() + 50  # start looking for YOU WIN after 50s

    while time.time() < battle_end_time:
        tap_ratio(*RATIO_ATTACK)
        if time.time() > start_searching_win:
            screen = screenshot()
            val, cx, cy = find_template(screen, "you_win.png")
            if val >= THRESHOLD:
                log("YOU WIN detected!")
                break
        time.sleep(CLICK_INTERVAL)

    # 7. Tap checkmark
    log("Step 7: Confirming YOU WIN")
    if not wait_and_tap("checkmark.png", timeout=15, delay_after=2.0):
        log("ERROR: Checkmark not found")
        return False

    # 8. Wait for return to starting screen
    log("Step 8: Waiting for starting screen")
    if wait_for("training.png", timeout=10) is None:
        log("WARNING: Starting screen did not appear, continuing anyway")

    log(f"Battle #{number} completed successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Pokemon GO Auto Battle Bot")
    parser.add_argument("--fights", type=int, default=0,
                        help="Number of fights (0 = infinite)")
    parser.add_argument("--minutes", type=int, default=0,
                        help="Runtime duration in minutes (0 = infinite)")
    args = parser.parse_args()

    # Check ADB connection
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    if "device" not in result.stdout:
        print("ERROR: Device is not connected or ADB is not running.")
        print("Run: adb devices")
        sys.exit(1)

    global SCREEN_W, SCREEN_H
    SCREEN_W, SCREEN_H = get_screen_resolution()
    log(f"Detected screen resolution: {SCREEN_W}x{SCREEN_H}")

    log("Bot started!")
    if args.fights:
        log(f"Target: {args.fights} fights")
    if args.minutes:
        log(f"Target: {args.minutes} minutes")
    log("Switch to the Battle screen in Pokemon GO. You have 5 seconds...")
    time.sleep(5)

    fight_number = 0
    errors = 0
    start_time = time.time()
    time_limit = args.minutes * 60 if args.minutes else 0

    try:
        while True:
            # Check limits
            if args.fights and fight_number >= args.fights:
                log(f"Reached limit of {args.fights} fights. Exiting.")
                break
            if time_limit and (time.time() - start_time) >= time_limit:
                log(f"Reached limit of {args.minutes} minutes. Exiting.")
                break

            fight_number += 1
            success = run_single_battle(fight_number)

            if not success:
                errors += 1
                log(f"Error in battle #{fight_number}. Total errors: {errors}")
                if errors >= 3:
                    log("3 consecutive errors. Stopping bot.")
                    break
                log("Waiting 10s and retrying...")
                time.sleep(10)
            else:
                errors = 0  # reset error counter on success
                time.sleep(1)  # brief pause between battles

    except KeyboardInterrupt:
        log("Stopped by user (Ctrl+C)")

    # Summary
    total_time = int(time.time() - start_time)
    log(f"═══ Summary ═══")
    log(f"Fights: {fight_number}")
    log(f"Time: {total_time // 60}m {total_time % 60}s")

    # System notifications
    if sys.platform.startswith("linux"):
        subprocess.run([
            "notify-send",
            "Pokemon GO Bot",
            f"Finished! Fights: {fight_number}, Time: {total_time // 60}m"
        ], stderr=subprocess.DEVNULL)
    else:
        log(f"Finished! Fights: {fight_number}, Time: {total_time // 60}m")


if __name__ == "__main__":
    main()