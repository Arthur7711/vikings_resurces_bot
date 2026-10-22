"""Grab the game window and crop a template image of something the bot should click.

Usage: python capture_template.py <name>
Drag a box around the icon, press ENTER/SPACE to save (C to cancel).
Templates are clicked in filename order, so prefix them: 01_food.png, 02_collect_btn.png ...
"""
import sys
from pathlib import Path

import cv2

import window

TEMPLATES = Path(__file__).parent / "templates"


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python capture_template.py <name>   (e.g. 01_wood_bubble)")
    name = sys.argv[1]
    TEMPLATES.mkdir(exist_ok=True)

    hwnd = window.find_window()
    window.focus(hwnd)
    img = window.capture(hwnd)

    x, y, w, h = cv2.selectROI("Drag a box around the icon, then press ENTER", img, showCrosshair=False)
    cv2.destroyAllWindows()
    if w == 0 or h == 0:
        sys.exit("Cancelled.")

    path = TEMPLATES / f"{name}.png"
    cv2.imwrite(str(path), img[y:y + h, x:x + w])
    print(f"Saved {path}  ({w}x{h}px)")


if __name__ == "__main__":
    main()
