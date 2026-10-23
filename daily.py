"""Daily reward: when the "Your daily reward" window is on screen, press its green Collect button.

The window pops up by itself once a day and covers everything, so it's checked before each round.
"""
import random
import time
from pathlib import Path

import cv2

import window

UI = Path(__file__).parent / "ui"
TITLE = cv2.imread(str(UI / "daily_reward.png"))      # "Your daily reward:" heading
COLLECT = cv2.imread(str(UI / "daily_collect.png"))   # green "Collect" button
THRESHOLD = 0.85


def find(screen, template):
    """Centre of the template on screen, or None if it isn't there."""
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, (x, y) = cv2.minMaxLoc(result)
    if score < THRESHOLD:
        return None
    h, w = template.shape[:2]
    return x + w // 2, y + h // 2


def run(hwnd):
    """Collect the daily reward if its window is open. Returns True if Collect was pressed."""
    collected = False
    for _ in range(3):
        screen = window.capture(hwnd)
        if find(screen, TITLE) is None:
            break
        button = find(screen, COLLECT)
        if button is None:
            print("  daily reward window is open but has no Collect button")
            break
        print("  collecting the daily reward")
        window.click(hwnd, *button, jitter=8)
        collected = True
        time.sleep(random.uniform(2.5, 3.5))
    if collected:
        time.sleep(3)  # the reward icon flies across the screen for a few seconds
    return collected
