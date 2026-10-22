"""Find the game window, capture it, and click inside it (Windows only)."""
import ctypes
import ctypes.wintypes as wt
import random
import time

import mss
import numpy as np

user32 = ctypes.windll.user32

# Make window/screen coordinates match real pixels on scaled (125%, 150%) displays.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()

WINDOW_TITLE = "Vikings at War"

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
SW_RESTORE = 9


def find_window(title_part=WINDOW_TITLE):
    """Return the handle of the first visible window whose title contains title_part."""
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if title_part.lower() in buf.value.lower():
                found.append(hwnd)
                return False
        return True

    user32.EnumWindows(callback, 0)
    if not found:
        raise RuntimeError(f"Game window '{title_part}' not found. Is the game running?")
    return found[0]


def client_rect(hwnd):
    """Screen rectangle (left, top, width, height) of the window's drawable area."""
    rect = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    pt = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, rect.right, rect.bottom


def focus(hwnd):
    """Bring the game to the front (screen capture and clicks only work on what's visible)."""
    if user32.GetForegroundWindow() == hwnd and not user32.IsIconic(hwnd):
        return
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)


_sct = mss.mss()


def capture(hwnd):
    """Return a BGR numpy image of the window's client area."""
    focus(hwnd)
    left, top, width, height = client_rect(hwnd)
    shot = _sct.grab({"left": left, "top": top, "width": width, "height": height})
    return np.array(shot)[:, :, :3].copy()


def drag(hwnd, x1, y1, x2, y2, steps=25):
    """Drag the map from (x1, y1) to (x2, y2) (client coords), holding at the end to stop inertia."""
    focus(hwnd)
    left, top, _, _ = client_rect(hwnd)
    user32.SetCursorPos(left + x1, top + y1)
    time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    for i in range(1, steps + 1):
        x = x1 + (x2 - x1) * i // steps
        y = y1 + (y2 - y1) * i // steps
        user32.SetCursorPos(left + x, top + y)
        time.sleep(0.015)
    time.sleep(0.3)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.8)


def click(hwnd, x, y, jitter=3):
    """Click at (x, y) relative to the window's client area, with small random jitter."""
    focus(hwnd)
    left, top, _, _ = client_rect(hwnd)
    sx = left + x + random.randint(-jitter, jitter)
    sy = top + y + random.randint(-jitter, jitter)
    user32.SetCursorPos(sx, sy)
    time.sleep(random.uniform(0.05, 0.12))
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(random.uniform(0.04, 0.09))
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
