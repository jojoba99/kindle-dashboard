#!/usr/bin/env python3
"""Render the Kindle dashboard data as a 758x1024 PNG screensaver."""

from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit(
        "Pillow is required to render the screensaver PNG. "
        "Install it in the runtime that executes this script."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "latest.json"
OUT_PATH = ROOT / "screensaver" / "kindle-dashboard.png"
W, H = 758, 1024


def font(size: int, bold: bool = False):
    candidates = [
        os.environ.get("KINDLE_DASHBOARD_FONT"),
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if path and Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size, index=0)
            except Exception:
                pass
    return ImageFont.load_default()


F = {
    "small": font(17),
    "body": font(20),
    "body2": font(22),
    "title": font(24),
    "mid": font(34),
    "large": font(56),
    "clock": font(78),
}


def draw_text(draw, xy, text, fnt, fill=30):
    draw.text(xy, str(text), font=fnt, fill=fill)


def line(draw, y, width=1):
    draw.line((20, y, W - 20, y), fill=70, width=width)


def short_condition(value):
    return str(value).replace("小毛毛雨", "小雨").replace("毛毛雨", "小雨").replace("大毛毛雨", "大雨")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    img = Image.new("L", (W, H), 247)
    draw = ImageDraw.Draw(img)

    city = data.get("city", "杭州")
    generated_at = data.get("generated_at", "").replace("T", " ")
    updated = generated_at[5:16]
    clock = generated_at[11:16] or "--:--"
    date = data.get("date", {})
    weather = data.get("weather", {})
    sun = data.get("sun", {})
    reminders = data.get("reminders", [])[:5]
    hourly = data.get("hourly_forecast", [])[:24]
    daily = data.get("daily_trend", [])[:7]

    y = 28
    draw_text(draw, (20, y), f"{city} · 数据 {updated}", F["body"], 30)
    draw_text(draw, (W - 120, y), "数据正常" if not data.get("stale") else "数据较旧", F["body"], 30)
    line(draw, 58, 2)

    y = 88
    draw_text(draw, (20, y), clock, F["clock"], 30)
    draw_text(draw, (522, y + 2), date.get("solar", ""), F["title"], 30)
    draw_text(draw, (544, y + 42), date.get("weekday", ""), F["mid"], 30)
    draw_text(draw, (548, y + 88), date.get("lunar", ""), F["body"], 80)
    draw_text(draw, (510, y + 118), date.get("ganzhi", ""), F["body"], 80)
    line(draw, 232)

    y = 250
    draw_text(draw, (20, y), "今日提醒", F["body"], 30)
    draw.line((20, y + 30, 110, y + 30), fill=70)
    x = 20
    for item in reminders:
        draw_text(draw, (x, y + 48), item.get("label", "--"), F["small"], 80)
        draw_text(draw, (x, y + 76), item.get("value", "--"), F["mid"], 30)
        x += 145
    line(draw, 372)

    y = 390
    draw_text(draw, (20, y), "天气", F["body"], 30)
    draw.line((20, y + 30, 74, y + 30), fill=70)
    draw_text(draw, (20, y + 54), round(float(weather.get("temperature", 0))), F["large"], 30)
    draw_text(draw, (88, y + 56), "°", F["mid"], 30)
    draw_text(draw, (126, y + 70), short_condition(weather.get("condition", "--")), F["mid"], 30)
    draw_text(draw, (20, y + 126), f"湿度 {weather.get('humidity', '--')}% · 降水 {weather.get('precipitation_probability', '--')}% · 体感 {round(float(weather.get('apparent_temperature', 0)))}°", F["body"], 80)
    draw_text(draw, (20, y + 158), weather.get("wind", "--"), F["body"], 80)

    draw.line((372, 386, 372, 552), fill=100)
    draw_text(draw, (398, y), "日出日落", F["body"], 30)
    draw.line((398, y + 30, 488, y + 30), fill=70)
    sunrise = str(sun.get("sunrise", "--"))[-5:]
    sunset = str(sun.get("sunset", "--"))[-5:]
    draw_text(draw, (398, y + 56), sunrise, F["mid"], 30)
    draw_text(draw, (518, y + 64), "日出", F["body"], 80)
    draw_text(draw, (398, y + 106), sunset, F["mid"], 30)
    draw_text(draw, (518, y + 114), "日落", F["body"], 80)
    draw_text(draw, (398, y + 154), f"白昼 {sun.get('daylight', '--')}", F["body"], 80)
    line(draw, 570)

    y = 586
    draw_text(draw, (20, y), "未来24小时", F["body"], 30)
    draw.line((20, y + 30, 130, y + 30), fill=70)
    col_w = 180
    row_h = 21
    for idx, item in enumerate(hourly):
        col = idx // 6
        row = idx % 6
        x = 20 + col * col_w
        yy = y + 48 + row * row_h
        draw_text(draw, (x, yy), item.get("time", "--"), F["small"], 80)
        draw_text(draw, (x + 44, yy), short_condition(item.get("condition", "--")), F["small"], 30)
        draw_text(draw, (x + 92, yy), f"{item.get('temperature', '--')}°", F["small"], 30)
        draw_text(draw, (x + 132, yy), f"{item.get('rain', '--')}%", F["small"], 80)
    line(draw, 758)

    y = 776
    draw_text(draw, (20, y), "未来7天", F["body"], 30)
    draw.line((20, y + 30, 104, y + 30), fill=70)
    col_w = 102
    for idx, item in enumerate(daily):
        x = 20 + idx * col_w
        if idx:
            draw.line((x - 10, y + 48, x - 10, y + 130), fill=130)
        draw_text(draw, (x, y + 48), item.get("day", "--"), F["small"], 80)
        draw_text(draw, (x, y + 74), short_condition(item.get("condition", "--")), F["body2"], 30)
        draw_text(draw, (x, y + 104), f"{item.get('high', '--')}/{item.get('low', '--')}°", F["small"], 80)
        draw_text(draw, (x, y + 128), f"{item.get('rain', '--')}%", F["small"], 80)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_PATH)
    print(f"rendered {OUT_PATH}")


if __name__ == "__main__":
    main()
