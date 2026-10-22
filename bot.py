"""Resource collector for Vikings at War (Google Play Games on PC).

Coins: scrolls over the whole city, finds every image from templates/ and clicks it (every 8-12 min).
Transports: starts/unloads trade transports for Amber, Iron, Cloth, Silver (every 30 s).

  python bot.py --transport   transports only
  python bot.py               transports + coins
  python bot.py --dry      only show what it would click on the current screen (no clicks)
  python bot.py --once     do one cycle and exit

Hold F8 to stop.
"""
import argparse
import ctypes
import random
import time
from pathlib import Path

import cv2
import numpy as np

import trade
import window

TEMPLATES = Path(__file__).parent / "templates"
THRESHOLD = 0.8           # match confidence 0..1; raise if it clicks wrong things, lower if it misses
SCALES = [s / 100 for s in range(70, 136, 5)]  # icons are bigger near the camera, smaller far away
CYCLE_MINUTES = (8, 12)   # random wait between cycles
MAX_PASSES = 10           # rescans per cycle (new icons may appear after a click)
STOP_KEY = 0x77           # F8
PAN_X, PAN_Y = 450, 260   # camera step in pixels; keep below screen size so views overlap
MOVE_DIFF = 12            # screen difference that counts as "the camera moved"
MAX_STEPS = 12            # safety limit on steps per row / number of rows
TRANSPORT_SECONDS = 30    # how often trade transports are checked


def stop_pressed():
    return ctypes.windll.user32.GetAsyncKeyState(STOP_KEY) & 0x8000


def load_templates():
    templates = []
    for path in sorted(TEMPLATES.glob("*.png")):
        img = cv2.imread(str(path))
        if img is None:
            continue
        if img.std() < 5:
            print(f"Skipping {path.name}: it's a flat colour and would match everywhere. Re-capture it.")
            continue
        templates.append((path.stem, img))
    return templates


def find_all(screen, template, threshold=THRESHOLD):
    """Return centre points of every place the template appears on screen, at any of SCALES."""
    candidates = []
    for scale in SCALES:
        tpl = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        h, w = tpl.shape[:2]
        if h > screen.shape[0] or w > screen.shape[1]:
            continue
        result = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
        result = np.nan_to_num(result, nan=-1, posinf=-1, neginf=-1)
        while True:
            _, score, _, (x, y) = cv2.minMaxLoc(result)
            if score < threshold:
                break
            candidates.append((x + w // 2, y + h // 2, score, max(w, h)))
            # Blank out this match so overlapping hits aren't reported twice.
            result[max(0, y - h // 2):y + h // 2 + 1, max(0, x - w // 2):x + w // 2 + 1] = -1

    # The same icon matches at several scales; keep only the best hit per spot.
    points = []
    for x, y, score, size in sorted(candidates, key=lambda c: -c[2]):
        if all(abs(x - px) > size // 2 or abs(y - py) > size // 2 for px, py, _ in points):
            points.append((x, y, score))
    return points


def moved(before, after):
    """True if the camera actually moved (water/smoke animation alone gives a diff of ~4-7)."""
    region = (slice(100, -90), slice(120, -110))  # ignore the top bar and side buttons
    return float(np.mean(cv2.absdiff(before[region], after[region]))) > MOVE_DIFF


def pan(hwnd, dx, dy):
    """Move the camera by dragging the map; dx>0 shows more to the right, dy>0 more below.
    Returns False if the camera was already at the city edge."""
    _, _, width, height = window.client_rect(hwnd)
    cx, cy = width // 2, height // 2
    before = window.capture(hwnd)
    window.drag(hwnd, cx + dx // 2, cy + dy // 2, cx - dx // 2, cy - dy // 2)
    return moved(before, window.capture(hwnd))


def sweep(hwnd, templates):
    """Visit the whole city row by row (snake pattern) and collect everything on the way."""
    print("  moving to the top-left corner...")
    for _ in range(MAX_STEPS):
        if stop_pressed() or not pan(hwnd, -PAN_X, -PAN_Y):
            break

    total, direction, view = 0, 1, 0
    for _ in range(MAX_STEPS):          # rows
        for _ in range(MAX_STEPS):      # views within a row
            if stop_pressed():
                return total
            view += 1
            n = run_cycle(hwnd, templates, dry=False)
            if n:
                print(f"  view {view}: {n} coin(s)")
            total += n
            if not pan(hwnd, direction * PAN_X, 0):
                break
        if not pan(hwnd, 0, PAN_Y):
            break                        # bottom edge reached
        direction = -direction
    return total


def run_cycle(hwnd, templates, dry):
    """Collect everything visible in the current view."""
    clicked = 0
    for _ in range(MAX_PASSES):
        if stop_pressed():
            return clicked
        screen = window.capture(hwnd)
        hit = None
        for name, tpl in templates:
            points = find_all(screen, tpl)
            if points:
                hit = (name, points)
                break
        if not hit:
            break

        name, points = hit
        if dry:
            for x, y, score in points:
                print(f"  would click {name} at ({x},{y}) score={score:.2f}")
                cv2.circle(screen, (x, y), 20, (0, 255, 0), 3)
            cv2.imshow("dry run - press any key", screen)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            return len(points)

        for x, y, score in points:
            if stop_pressed():
                return clicked
            print(f"  click {name} at ({x},{y}) score={score:.2f}")
            window.click(hwnd, x, y)
            clicked += 1
            time.sleep(random.uniform(0.6, 1.2))
        time.sleep(random.uniform(1.0, 1.8))  # let popups/animations settle before rescanning
    return clicked


def wait(seconds):
    """Sleep, but return False early if F8 is pressed."""
    end = time.time() + seconds
    while time.time() < end:
        if stop_pressed():
            return False
        time.sleep(0.2)
    return True


def check_transports(hwnd):
    print(time.strftime("[%H:%M:%S]"), "checking trade transports...")
    t = trade.run(hwnd, stop_pressed)
    print(f"  {t} transport/sell action(s)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", action="store_true", help="only trade transports, every 30 s")
    parser.add_argument("--dry", action="store_true", help="show matches without clicking")
    parser.add_argument("--once", action="store_true", help="run a single cycle")
    args = parser.parse_args()

    hwnd = window.find_window()
    print("Hold F8 to stop.")

    if args.transport:
        while True:
            check_transports(hwnd)
            if args.once or not wait(TRANSPORT_SECONDS):
                break
        print("Stopped.")
        return

    templates = load_templates()
    if not templates:
        raise SystemExit("No templates yet. Make some with: python capture_template.py 01_name")
    print("Templates:", ", ".join(name for name, _ in templates))

    if args.dry:
        window.focus(hwnd)
        run_cycle(hwnd, templates, dry=True)
        return

    next_coins = 0
    while True:
        if time.time() >= next_coins:
            print(time.strftime("[%H:%M:%S]"), "collecting coins...")
            n = sweep(hwnd, templates)
            print(f"  done, collected {n} coin(s) this round")
            next_coins = time.time() + random.uniform(*CYCLE_MINUTES) * 60
            print(f"  next coin round in {(next_coins - time.time()) / 60:.1f} min")
        if stop_pressed():
            break
        check_transports(hwnd)
        if args.once or not wait(TRANSPORT_SECONDS):
            break
    print("Stopped.")


if __name__ == "__main__":
    main()
