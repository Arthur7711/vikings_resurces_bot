"""Trade goods (Amber, Iron, Cloth, Silver): start/unload transports and sell what's delivered.

Opens the trade window from the top bar, visits every resource tab and presses:
- the left action button only when it is the green "Start transport" / "Unload transport" button;
- "Sell now" only when it is bright green (there's something to sell; dark green means 0).
Orange "Speed up for N Coins", "N Coins", ad buttons and "Upgrade" are never clicked.
"""
import random
import time
from pathlib import Path

import cv2
import numpy as np

import window

UI = Path(__file__).parent / "ui"

# Positions in the game window (1310x735 client area). Top-bar icons and the close
# button are anchored to the right edge, so they're stored as offsets from it.
TOPBAR_ICON_FROM_RIGHT = 413          # the first trade-goods icon in the top bar
TOPBAR_Y = 62
TABS = {"Amber": (110, 140), "Iron": (110, 232), "Cloth": (110, 320), "Silver": (110, 412)}
ACTION_BUTTON = (447, 315)            # centre of the left action button
ACTION_SAMPLES = [(x, y) for x in range(190, 710, 40) for y in (298, 334)]  # above/below the text
SELL_BUTTON = (1022, 315)             # centre of "Sell now"
SELL_SAMPLES = [(x, y) for x in range(770, 1290, 40) for y in (298, 334)]
CLOSE_FROM_RIGHT = 29
CLOSE_Y = 66

GREEN = np.array([90, 178, 90])       # BGR of the active green buttons
COLOR_TOLERANCE = 30


def is_green(pixel):
    return np.abs(pixel.astype(int) - GREEN).max() <= COLOR_TOLERANCE


def dialog_open(screen):
    """True if the trade window (its close button) is on screen."""
    close = cv2.imread(str(UI / "close.png"))
    x = screen.shape[1] - CLOSE_FROM_RIGHT
    area = screen[CLOSE_Y - 40:CLOSE_Y + 40, x - 40:x + 40]
    score = cv2.matchTemplate(area, close, cv2.TM_CCOEFF_NORMED).max()
    return score > 0.8


def action_ready(screen):
    """True if the left action button is the green Start/Unload transport button."""
    return all(is_green(screen[y, x]) for x, y in ACTION_SAMPLES)


def sell_ready(screen):
    """True if "Sell now" is bright green, i.e. there are goods to sell."""
    return all(is_green(screen[y, x]) for x, y in SELL_SAMPLES)


def run(hwnd, stop_pressed=lambda: False):
    """Visit every trade tab, start/unload transports and sell. Returns the number of actions."""
    _, _, width, _ = window.client_rect(hwnd)
    if not dialog_open(window.capture(hwnd)):
        window.click(hwnd, width - TOPBAR_ICON_FROM_RIGHT, TOPBAR_Y, jitter=2)
        time.sleep(2)
    if not dialog_open(window.capture(hwnd)):
        print("  trade window didn't open, skipping")
        return 0

    actions = 0
    for name, (x, y) in TABS.items():
        if stop_pressed():
            break
        window.click(hwnd, x, y, jitter=2)
        time.sleep(random.uniform(1.2, 1.8))
        # Unloading can be followed straight away by a new transport, so check a few times.
        for _ in range(4):
            screen = window.capture(hwnd)
            if not dialog_open(screen):
                break
            if action_ready(screen):
                print(f"  {name}: pressing the green transport button")
                window.click(hwnd, *ACTION_BUTTON, jitter=8)
            elif sell_ready(screen):
                print(f"  {name}: selling")
                window.click(hwnd, *SELL_BUTTON, jitter=8)
            else:
                break
            actions += 1
            time.sleep(random.uniform(2.0, 3.0))
        if not dialog_open(screen):
            print(f"  {name}: something covered the trade window, stopping here")
            break

    window.click(hwnd, width - CLOSE_FROM_RIGHT, CLOSE_Y, jitter=2)
    time.sleep(1.5)
    return actions
