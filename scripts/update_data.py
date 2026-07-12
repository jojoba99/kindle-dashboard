#!/usr/bin/env python3
"""Generate Kindle dashboard data and prerender index.html.

The script intentionally uses only Python standard-library modules so GitHub
Actions can run it without installing dependencies.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "latest.json"
INDEX_PATH = ROOT / "index.html"
TZ = ZoneInfo("Asia/Shanghai")

CITY = {
    "name": "杭州",
    "latitude": 30.2741,
    "longitude": 120.1551,
}

WEATHER_CODES = {
    0: "晴",
    1: "大致晴",
    2: "少云",
    3: "阴",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "大毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "阵雨",
    81: "强阵雨",
    82: "暴阵雨",
    85: "阵雪",
    86: "强阵雪",
    95: "雷雨",
    96: "雷雨冰雹",
    99: "强雷雨冰雹",
}

WIND_NAMES = ["北风", "东北风", "东风", "东南风", "南风", "西南风", "西风", "西北风"]

LUNAR_INFO = [
    0x04BD8, 0x04AE0, 0x0A570, 0x054D5, 0x0D260, 0x0D950, 0x16554, 0x056A0, 0x09AD0, 0x055D2,
    0x04AE0, 0x0A5B6, 0x0A4D0, 0x0D250, 0x1D255, 0x0B540, 0x0D6A0, 0x0ADA2, 0x095B0, 0x14977,
    0x04970, 0x0A4B0, 0x0B4B5, 0x06A50, 0x06D40, 0x1AB54, 0x02B60, 0x09570, 0x052F2, 0x04970,
    0x06566, 0x0D4A0, 0x0EA50, 0x06E95, 0x05AD0, 0x02B60, 0x186E3, 0x092E0, 0x1C8D7, 0x0C950,
    0x0D4A0, 0x1D8A6, 0x0B550, 0x056A0, 0x1A5B4, 0x025D0, 0x092D0, 0x0D2B2, 0x0A950, 0x0B557,
    0x06CA0, 0x0B550, 0x15355, 0x04DA0, 0x0A5D0, 0x14573, 0x052D0, 0x0A9A8, 0x0E950, 0x06AA0,
    0x0AEA6, 0x0AB50, 0x04B60, 0x0AAE4, 0x0A570, 0x05260, 0x0F263, 0x0D950, 0x05B57, 0x056A0,
    0x096D0, 0x04DD5, 0x04AD0, 0x0A4D0, 0x0D4D4, 0x0D250, 0x0D558, 0x0B540, 0x0B6A0, 0x195A6,
    0x095B0, 0x049B0, 0x0A974, 0x0A4B0, 0x0B27A, 0x06A50, 0x06D40, 0x0AF46, 0x0AB60, 0x09570,
    0x04AF5, 0x04970, 0x064B0, 0x074A3, 0x0EA50, 0x06B58, 0x055C0, 0x0AB60, 0x096D5, 0x092E0,
    0x0C960, 0x0D954, 0x0D4A0, 0x0DA50, 0x07552, 0x056A0, 0x0ABB7, 0x025D0, 0x092D0, 0x0CAB5,
    0x0A950, 0x0B4A0, 0x0BAA4, 0x0AD50, 0x055D9, 0x04BA0, 0x0A5B0, 0x15176, 0x052B0, 0x0A930,
    0x07954, 0x06AA0, 0x0AD50, 0x05B52, 0x04B60, 0x0A6E6, 0x0A4E0, 0x0D260, 0x0EA65, 0x0D530,
    0x05AA0, 0x076A3, 0x096D0, 0x04BD7, 0x04AD0, 0x0A4D0, 0x1D0B6, 0x0D250, 0x0D520, 0x0DD45,
    0x0B5A0, 0x056D0, 0x055B2, 0x049B0, 0x0A577, 0x0A4B0, 0x0AA50, 0x1B255, 0x06D20, 0x0ADA0,
]

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
ANIMALS = "鼠牛虎兔龙蛇马羊猴鸡狗猪"
MONTH_NAMES = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]
DAY_NAMES = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
             "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
             "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"]


def fetch_json(url: str, timeout: int = 15, headers: dict | None = None) -> dict:
    request_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 KindleDashboard/1.0",
        "Accept": "application/json,text/plain,*/*",
    }
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(url, headers=request_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
            return json.loads(resp.read().decode("utf-8"))


def load_previous() -> dict:
    if not DATA_PATH.exists():
        return {}
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def lunar_year_days(year: int) -> int:
    total = 348
    info = LUNAR_INFO[year - 1900]
    mask = 0x8000
    while mask > 0x8:
        if info & mask:
            total += 1
        mask >>= 1
    return total + leap_days(year)


def leap_month(year: int) -> int:
    return LUNAR_INFO[year - 1900] & 0xF


def leap_days(year: int) -> int:
    if leap_month(year):
        return 30 if (LUNAR_INFO[year - 1900] & 0x10000) else 29
    return 0


def month_days(year: int, month: int) -> int:
    return 30 if (LUNAR_INFO[year - 1900] & (0x10000 >> month)) else 29


def solar_to_lunar(day: dt.date) -> dict:
    base = dt.date(1900, 1, 31)
    offset = (day - base).days
    year = 1900
    while year < 2050:
        days = lunar_year_days(year)
        if offset < days:
            break
        offset -= days
        year += 1

    leap = leap_month(year)
    is_leap = False
    month = 1
    while month <= 12:
        days = leap_days(year) if is_leap else month_days(year, month)
        if offset < days:
            break
        offset -= days
        if leap == month and not is_leap:
            is_leap = True
        else:
            if is_leap:
                is_leap = False
            month += 1

    lunar_day = offset + 1
    return {"year": year, "month": month, "day": lunar_day, "is_leap": is_leap}


def ganzhi(index: int) -> str:
    return GAN[index % 10] + ZHI[index % 12]


def build_date(now: dt.datetime) -> dict:
    day = now.date()
    lunar = solar_to_lunar(day)
    year_gz = ganzhi(lunar["year"] - 4)
    month_gz = ganzhi((now.year - 1900) * 12 + now.month + 12)
    day_gz = ganzhi((day - dt.date(1900, 1, 1)).days + 10)
    leap = "闰" if lunar["is_leap"] else ""
    lunar_text = "农历%s%s月%s" % (leap, MONTH_NAMES[lunar["month"] - 1], DAY_NAMES[lunar["day"] - 1])
    weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][day.weekday()]
    animal = ANIMALS[(lunar["year"] - 4) % 12]
    return {
        "solar": day.strftime("%Y / %m / %d"),
        "weekday": weekday,
        "lunar": lunar_text,
        "ganzhi": "%s%s年 %s月 %s日" % (year_gz, animal, month_gz, day_gz),
        "festival": "",
    }


def build_almanac(now: dt.datetime) -> dict:
    yi_pool = ["整理", "阅读", "沐浴", "散步", "纳财", "会友", "学习", "早睡", "修整", "出行"]
    ji_pool = ["熬夜", "久坐", "拖延", "暴食", "争执", "远行", "冒雨", "冲动", "贪凉", "迟到"]
    seed = int(now.strftime("%Y%m%d"))
    return {
        "yi": [yi_pool[(seed + i * 3) % len(yi_pool)] for i in range(3)],
        "ji": [ji_pool[(seed + i * 4) % len(ji_pool)] for i in range(3)],
    }


def wind_label(direction: float | int | None, speed: float | int | None) -> str:
    if direction is None or speed is None:
        return "--"
    idx = int((float(direction) + 22.5) // 45) % 8
    return "%s %.0fkm/h" % (WIND_NAMES[idx], float(speed))


def fetch_weather(previous: dict) -> tuple[dict, dict, dict, list[dict], list[dict], list[dict], bool]:
    params = {
        "latitude": CITY["latitude"],
        "longitude": CITY["longitude"],
        "timezone": "Asia/Shanghai",
        "forecast_days": 7,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m",
        "hourly": "weather_code,precipitation_probability,relative_humidity_2m,temperature_2m,apparent_temperature,uv_index",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,daylight_duration,uv_index_max,precipitation_probability_max",
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    try:
        raw = fetch_json(url)
        current = raw.get("current", {})
        daily = raw.get("daily", {})
        weather = {
            "temperature": current.get("temperature_2m"),
            "condition": WEATHER_CODES.get(int(current.get("weather_code", 0)), "未知"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation_probability": first(daily.get("precipitation_probability_max"), 0),
            "wind": wind_label(current.get("wind_direction_10m"), current.get("wind_speed_10m")),
            "uv_index": first(daily.get("uv_index_max"), 0),
            "apparent_temperature": current.get("apparent_temperature"),
        }
        daylight_seconds = first(daily.get("daylight_duration"), 0) or 0
        sun = {
            "sunrise": first(daily.get("sunrise"), ""),
            "sunset": first(daily.get("sunset"), ""),
            "daylight": format_duration(daylight_seconds),
        }
        outing = build_outing(weather)
        reminders = build_reminders(weather, outing)
        hourly = build_hourly_forecast(raw)
        daily_trend = build_daily_trend(raw)
        return weather, sun, outing, reminders, hourly, daily_trend, True
    except Exception as exc:
        print("weather fetch failed: %s" % exc, file=sys.stderr)
        return (
            previous.get("weather") or fallback_weather(),
            previous.get("sun") or fallback_sun(),
            previous.get("outing") or build_outing(fallback_weather()),
            previous.get("reminders") or build_reminders(fallback_weather(), build_outing(fallback_weather())),
            previous.get("hourly_forecast") or fallback_hourly(),
            previous.get("daily_trend") or fallback_daily_trend(),
            False,
        )


def first(value, default=None):
    if isinstance(value, list) and value:
        return value[0]
    if value is None:
        return default
    return value


def format_duration(seconds: float | int) -> str:
    minutes = int(round(float(seconds) / 60))
    return "%d小时%02d分" % (minutes // 60, minutes % 60)


def build_outing(weather: dict) -> dict:
    rain = pct(weather.get("precipitation_probability"))
    temp = float_or(weather.get("temperature"), 26)
    apparent = float_or(weather.get("apparent_temperature"), temp)
    humidity = pct(weather.get("humidity"))
    uv = min(100, int(float_or(weather.get("uv_index"), 0) / 11 * 100))

    if rain >= 60:
        umbrella = "要带"
    elif rain >= 35:
        umbrella = "备着"
    else:
        umbrella = "不用"

    if apparent >= 30:
        clothing = "短袖"
    elif apparent >= 23:
        clothing = "薄衫"
    elif apparent >= 15:
        clothing = "外套"
    else:
        clothing = "厚外套"

    notes = []
    if rain >= 35:
        notes.append("可能有雨")
    if humidity >= 75 and apparent >= 26:
        notes.append("体感闷热")
    if uv >= 55:
        notes.append("注意防晒")
    if apparent >= 34:
        notes.append("减少暴晒")
    if not notes:
        notes.append("轻装出门")

    comfort = 100 - min(55, abs(apparent - 24) * 5) - max(0, humidity - 70) * 0.6 - rain * 0.25
    comfort = int(max(0, min(100, round(comfort))))

    if comfort >= 75 and rain < 35:
        summary = "适合出门"
    elif comfort >= 55:
        summary = "正常出门"
    else:
        summary = "谨慎安排"

    return {
        "umbrella": umbrella,
        "clothing": clothing,
        "summary": summary,
        "scores": {
            "rain": rain,
            "comfort": comfort,
            "humidity": humidity,
            "uv": uv,
        },
        "notes": notes[:3],
    }


def build_reminders(weather: dict, outing: dict) -> list[dict]:
    rain = pct(weather.get("precipitation_probability"))
    humidity = pct(weather.get("humidity"))
    wind = extract_wind_speed(weather.get("wind"))
    apparent = float_or(weather.get("apparent_temperature"), float_or(weather.get("temperature"), 26))
    uv = float_or(weather.get("uv_index"), 0)

    if rain >= 60:
        laundry = "不建议"
    elif humidity >= 75:
        laundry = "较慢"
    elif wind >= 18:
        laundry = "可晾"
    else:
        laundry = "普通"

    if rain >= 50:
        ventilate = "短时"
    elif humidity >= 80:
        ventilate = "除湿"
    elif wind >= 28:
        ventilate = "小开"
    else:
        ventilate = "适合"

    if rain >= 50:
        exercise = "室内"
    elif apparent >= 33:
        exercise = "避暑"
    elif apparent <= 8:
        exercise = "保暖"
    else:
        exercise = "户外"

    if uv >= 6:
        sunscreen = "要做"
    elif uv >= 3:
        sunscreen = "适量"
    else:
        sunscreen = "普通"

    return [
        {"label": "带伞", "value": outing.get("umbrella", "--")},
        {"label": "洗衣", "value": laundry},
        {"label": "通风", "value": ventilate},
        {"label": "运动", "value": exercise},
        {"label": "防晒", "value": sunscreen},
    ]


def build_hourly_forecast(raw: dict) -> list[dict]:
    hourly = raw.get("hourly", {})
    times = hourly.get("time") or []
    temperatures = hourly.get("temperature_2m") or []
    apparent = hourly.get("apparent_temperature") or []
    rain = hourly.get("precipitation_probability") or []
    codes = hourly.get("weather_code") or []
    now = dt.datetime.now(TZ).replace(minute=0, second=0, microsecond=0)
    rows = []
    for idx, value in enumerate(times):
        try:
            hour = dt.datetime.fromisoformat(value).replace(tzinfo=TZ)
        except ValueError:
            continue
        if hour < now:
            continue
        rows.append({
            "time": hour.strftime("%H时"),
            "condition": WEATHER_CODES.get(int(first_at(codes, idx, 0)), "未知"),
            "temperature": round(float_or(first_at(temperatures, idx, 0), 0)),
            "apparent_temperature": round(float_or(first_at(apparent, idx, 0), 0)),
            "rain": pct(first_at(rain, idx, 0)),
        })
        if len(rows) >= 24:
            break
    return rows


def build_daily_trend(raw: dict) -> list[dict]:
    daily = raw.get("daily", {})
    times = daily.get("time") or []
    highs = daily.get("temperature_2m_max") or []
    lows = daily.get("temperature_2m_min") or []
    rain = daily.get("precipitation_probability_max") or []
    codes = daily.get("weather_code") or []
    names = ["今", "明", "后", "周三", "周四", "周五", "周六"]
    rows = []
    for idx, value in enumerate(times[:7]):
        label = names[idx] if idx < len(names) else value[5:]
        if idx >= 3:
            try:
                day = dt.date.fromisoformat(value)
                label = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][day.weekday()]
            except ValueError:
                label = value[5:]
        rows.append({
            "day": label,
            "condition": WEATHER_CODES.get(int(first_at(codes, idx, 0)), "未知"),
            "high": round(float_or(first_at(highs, idx, 0), 0)),
            "low": round(float_or(first_at(lows, idx, 0), 0)),
            "rain": pct(first_at(rain, idx, 0)),
        })
    return rows


def first_at(values, index: int, default=None):
    if isinstance(values, list) and 0 <= index < len(values):
        return values[index]
    return default


def extract_wind_speed(value) -> float:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)km/h", str(value or ""))
    if not match:
        return 0
    return float_or(match.group(1), 0)


def pct(value) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, number))


def float_or(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fallback_weather() -> dict:
    return {
        "temperature": 30,
        "condition": "晴",
        "humidity": 62,
        "precipitation_probability": 16,
        "wind": "东南风 8km/h",
        "uv_index": 7.5,
        "apparent_temperature": 33,
    }


def fallback_sun() -> dict:
    return {"sunrise": "05:06", "sunset": "19:04", "daylight": "13小时58分"}


def fallback_hourly() -> list[dict]:
    return [
        {"time": "17时", "condition": "小雨", "temperature": 29, "apparent_temperature": 33, "rain": 100},
        {"time": "18时", "condition": "小雨", "temperature": 28, "apparent_temperature": 32, "rain": 95},
        {"time": "19时", "condition": "阴", "temperature": 28, "apparent_temperature": 31, "rain": 80},
        {"time": "20时", "condition": "阴", "temperature": 27, "apparent_temperature": 30, "rain": 65},
        {"time": "21时", "condition": "阴", "temperature": 27, "apparent_temperature": 30, "rain": 55},
        {"time": "22时", "condition": "阴", "temperature": 27, "apparent_temperature": 30, "rain": 45},
        {"time": "23时", "condition": "阴", "temperature": 26, "apparent_temperature": 29, "rain": 40},
        {"time": "00时", "condition": "阴", "temperature": 26, "apparent_temperature": 29, "rain": 35},
        {"time": "01时", "condition": "阴", "temperature": 26, "apparent_temperature": 29, "rain": 30},
        {"time": "02时", "condition": "阴", "temperature": 26, "apparent_temperature": 29, "rain": 28},
        {"time": "03时", "condition": "阴", "temperature": 25, "apparent_temperature": 28, "rain": 25},
        {"time": "04时", "condition": "阴", "temperature": 25, "apparent_temperature": 28, "rain": 22},
        {"time": "05时", "condition": "阴", "temperature": 25, "apparent_temperature": 28, "rain": 20},
        {"time": "06时", "condition": "阴", "temperature": 25, "apparent_temperature": 28, "rain": 20},
        {"time": "07时", "condition": "阴", "temperature": 26, "apparent_temperature": 29, "rain": 22},
        {"time": "08时", "condition": "阴", "temperature": 27, "apparent_temperature": 30, "rain": 25},
        {"time": "09时", "condition": "阴", "temperature": 28, "apparent_temperature": 31, "rain": 28},
        {"time": "10时", "condition": "阴", "temperature": 29, "apparent_temperature": 32, "rain": 30},
        {"time": "11时", "condition": "阴", "temperature": 30, "apparent_temperature": 33, "rain": 32},
        {"time": "12时", "condition": "阴", "temperature": 31, "apparent_temperature": 34, "rain": 35},
        {"time": "13时", "condition": "阴", "temperature": 31, "apparent_temperature": 34, "rain": 38},
        {"time": "14时", "condition": "阴", "temperature": 31, "apparent_temperature": 34, "rain": 40},
        {"time": "15时", "condition": "阴", "temperature": 30, "apparent_temperature": 33, "rain": 42},
        {"time": "16时", "condition": "阴", "temperature": 30, "apparent_temperature": 33, "rain": 45},
    ]


def fallback_daily_trend() -> list[dict]:
    return [
        {"day": "今", "condition": "小雨", "high": 29, "low": 25, "rain": 100},
        {"day": "明", "condition": "雨", "high": 31, "low": 25, "rain": 75},
        {"day": "后", "condition": "阴", "high": 33, "low": 26, "rain": 45},
        {"day": "周三", "condition": "阴", "high": 33, "low": 26, "rain": 35},
        {"day": "周四", "condition": "小雨", "high": 32, "low": 25, "rain": 55},
        {"day": "周五", "condition": "阴", "high": 34, "low": 26, "rain": 30},
        {"day": "周六", "condition": "晴", "high": 35, "low": 27, "rain": 15},
    ]


def render_index(data: dict) -> None:
    html = INDEX_PATH.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, indent=6)
    replacement = "window.__KINDLE_DATA__ = %s;" % payload
    html = re.sub(r"window\.__KINDLE_DATA__ = \{.*?\};", replacement, html, count=1, flags=re.S)
    INDEX_PATH.write_text(html, encoding="utf-8")


def main() -> None:
    now = dt.datetime.now(TZ)
    previous = load_previous()
    weather, sun, outing, reminders, hourly, daily_trend, weather_ok = fetch_weather(previous)
    stale = not weather_ok

    data = {
        "city": CITY["name"],
        "generated_at": now.isoformat(timespec="seconds"),
        "stale": stale,
        "date": build_date(now),
        "reminders": reminders,
        "weather": weather,
        "sun": sun,
        "hourly_forecast": hourly,
        "daily_trend": daily_trend,
    }

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_index(data)
    print("generated %s for %s" % (DATA_PATH, data["city"]))


if __name__ == "__main__":
    main()
