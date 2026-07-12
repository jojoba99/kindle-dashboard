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


def fetch_weather(previous: dict) -> tuple[dict, dict, dict, bool]:
    params = {
        "latitude": CITY["latitude"],
        "longitude": CITY["longitude"],
        "timezone": "Asia/Shanghai",
        "forecast_days": 1,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m",
        "hourly": "precipitation_probability,relative_humidity_2m,temperature_2m,uv_index",
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
        return weather, sun, outing, True
    except Exception as exc:
        print("weather fetch failed: %s" % exc, file=sys.stderr)
        return (
            previous.get("weather") or fallback_weather(),
            previous.get("sun") or fallback_sun(),
            previous.get("outing") or build_outing(fallback_weather()),
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


def fetch_hotsearch(previous: dict) -> tuple[list[dict], bool]:
    endpoints = [
        (
            "https://weibo.com/ajax/statuses/hot_band",
            {"Referer": "https://weibo.com/hot/search"},
        ),
        (
            "https://weibo.com/ajax/side/hotSearch",
            {"Referer": "https://weibo.com/"},
        ),
        ("https://api.vvhan.com/api/hotlist/wbHot", {}),
        ("https://api-hot.imsyy.top/weibo", {}),
    ]
    for url, headers in endpoints:
        try:
            raw = fetch_json(url, headers=headers)
            parsed = parse_hotsearch(raw)
            if parsed:
                return parsed[:6], True
        except Exception as exc:
            print("hotsearch fetch failed from %s: %s" % (url, exc), file=sys.stderr)
    old = previous.get("hotsearch") or []
    if old:
        return old[:6], False
    return [
        {"rank": 1, "title": "微博热搜接口暂不可用", "hot": ""},
        {"rank": 2, "title": "天气与黄历仍可显示", "hot": ""},
        {"rank": 3, "title": "下次定时任务会重试", "hot": ""},
        {"rank": 4, "title": "Kindle 页面保持可读", "hot": ""},
        {"rank": 5, "title": "数据失败自动兜底", "hot": ""},
        {"rank": 6, "title": "无需 Mac 常开", "hot": ""},
    ], False


def parse_hotsearch(raw: dict) -> list[dict]:
    candidates = raw.get("data") if isinstance(raw, dict) else None
    if isinstance(candidates, dict):
        for key in ("band_list", "realtime", "list", "cards"):
            if isinstance(candidates.get(key), list):
                candidates = candidates[key]
                break
    if not isinstance(candidates, list):
        return []
    result = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        if item.get("is_ad") or item.get("ad_type"):
            continue
        title = item.get("title") or item.get("name") or item.get("word") or item.get("note")
        if not title:
            continue
        title = str(title).strip().strip("#")
        if not title:
            continue
        hot = item.get("hot") or item.get("num") or item.get("raw_hot") or ""
        result.append({"rank": len(result) + 1, "title": title, "hot": str(hot)})
        if len(result) >= 6:
            break
    return result


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


def render_index(data: dict) -> None:
    html = INDEX_PATH.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, indent=6)
    replacement = "window.__KINDLE_DATA__ = %s;" % payload
    html = re.sub(r"window\.__KINDLE_DATA__ = \{.*?\};", replacement, html, count=1, flags=re.S)
    INDEX_PATH.write_text(html, encoding="utf-8")


def main() -> None:
    now = dt.datetime.now(TZ)
    previous = load_previous()
    weather, sun, outing, weather_ok = fetch_weather(previous)
    hotsearch, hotsearch_ok = fetch_hotsearch(previous)
    stale = not (weather_ok and hotsearch_ok)

    data = {
        "city": CITY["name"],
        "generated_at": now.isoformat(timespec="seconds"),
        "stale": stale,
        "date": build_date(now),
        "almanac": build_almanac(now),
        "outing": outing,
        "weather": weather,
        "sun": sun,
        "hotsearch": hotsearch,
    }

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_index(data)
    print("generated %s for %s" % (DATA_PATH, data["city"]))


if __name__ == "__main__":
    main()
