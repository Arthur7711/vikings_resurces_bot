# Vikings at War resource bot

Clicks resource icons in the game (Google Play Games on PC) on a timer, using screenshots and image matching. The game itself is never modified.

## Setup
```
pip install -r requirements.txt
```

## 1. Teach it what to click
With the game open, run once per icon and drag a box around it:
```
python capture_template.py 01_food
python capture_template.py 02_wood
python capture_template.py 03_collect_button
```
Images go to `templates/` and are checked in filename order. Crop tightly around the icon only, with no changing numbers or background.

## 2. Test
```
python bot.py --dry
```
This shows green circles where it would click, without clicking.

## 3. Run
Transports and selling only, checked every minute:
```
python bot.py --transport
```
Transports and selling every minute, plus coins every hour:
```
python bot.py
```

For coins, it scrolls to the top-left corner of the city, then sweeps it row by row: right, down, left, down, and so on. It detects the city edges by itself and clicks every match in every view, then prints how many it collected.

For transports, it opens the trade window from the top bar and checks Amber, Iron, Cloth and Silver. It presses the green **Start transport** or **Unload transport** button when one is available, and **Sell now** when there are goods to sell. It never presses the orange **Speed up** or **N Coins** buttons, the ad button or "Upgrade".

Hold **F8** to stop. While it runs it takes over the mouse and brings the game to the front.

## Tips
- Keep the game window the same size you used for capturing templates.
- If it misses icons, lower `THRESHOLD` in `bot.py`. If it clicks wrong things, raise it.
- `CYCLE_MINUTES` controls how often it collects.
- `PAN_X` / `PAN_Y` set the camera step. Make them smaller if it misses coins between views.
