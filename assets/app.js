(function () {
  var data = window.__KINDLE_DATA__ || {};

  function byId(id) {
    return document.getElementById(id);
  }

  function text(id, value) {
    var el = byId(id);
    if (el) {
      el.innerHTML = value == null || value === "" ? "--" : String(value);
    }
  }

  function pad(value) {
    return value < 10 ? "0" + value : String(value);
  }

  function updateClock() {
    var now = new Date();
    text("clock", pad(now.getHours()) + ":" + pad(now.getMinutes()));
  }

  function pct(value) {
    var number = Number(value);
    if (isNaN(number)) {
      return 0;
    }
    if (number < 0) {
      return 0;
    }
    if (number > 100) {
      return 100;
    }
    return number;
  }

  function setBar(id, value) {
    var el = byId(id);
    if (el) {
      el.style.width = pct(value) + "%";
    }
  }

  function joinList(list) {
    if (!list || !list.length) {
      return "--";
    }
    return list.join("、");
  }

  function shortTime(value) {
    if (!value) {
      return "--";
    }
    var s = String(value);
    var t = s.indexOf("T");
    if (t >= 0) {
      return s.slice(t + 1, t + 6);
    }
    return s.slice(0, 5);
  }

  function render(nextData) {
    data = nextData || data || {};
    var date = data.date || {};
    var reminders = data.reminders || [];
    var outing = data.outing || {};
    var scores = outing.scores || {};
    var weather = data.weather || {};
    var sun = data.sun || {};
    var hourly = data.hourly_forecast || [];
    var dailyTrend = data.daily_trend || [];

    text("city", data.city || "杭州");
    text("updated", data.generated_at ? "数据 " + String(data.generated_at).replace("T", " ").slice(5, 16) : "离线预览");
    text("status", data.stale ? "数据较旧" : "数据正常");
    text("solar", date.solar);
    text("weekday", date.weekday);
    text("lunar", date.lunar);
    text("ganzhi", date.ganzhi);
    renderReminders(reminders);
    text("umbrella", outing.umbrella);
    text("clothing", outing.clothing);

    setBar("bar-rain", scores.rain);
    setBar("bar-comfort", scores.comfort);
    setBar("bar-humidity", scores.humidity);
    setBar("bar-uv", scores.uv);
    text("rain-value", pct(scores.rain) + "%");
    text("comfort-value", pct(scores.comfort));
    text("humidity-value", pct(scores.humidity) + "%");
    text("uv-value", pct(scores.uv));
    text("outing-notes", outing.summary ? outing.summary + " · " + joinList(outing.notes || []) : joinList(outing.notes || []));

    text("temperature", Math.round(Number(weather.temperature || 0)));
    text("condition", weather.condition);
    text("weather-detail", "湿度 " + (weather.humidity == null ? "--" : weather.humidity + "%") + " · 降水 " + (weather.precipitation_probability == null ? "--" : weather.precipitation_probability + "%") + " · 体感 " + (weather.apparent_temperature == null ? "--" : Math.round(weather.apparent_temperature) + "°"));
    text("wind", weather.wind || "--");
    text("daily-trend", formatDailyTrend(dailyTrend));

    text("sunrise", shortTime(sun.sunrise));
    text("sunset", shortTime(sun.sunset));
    text("daylight", sun.daylight ? "白昼 " + sun.daylight : "白昼 --");
    renderHourly(hourly);
  }

  function renderReminders(reminders) {
    var list = byId("reminder-list");
    if (list) {
      var html = "";
      var i;
      for (i = 0; i < reminders.length && i < 5; i += 1) {
        html += "<div class=\"reminder-item\"><span>" + escapeHtml(reminders[i].label || "--") + "</span><strong>" + escapeHtml(reminders[i].value || "--") + "</strong></div>";
      }
      list.innerHTML = html || "<div class=\"reminder-item\"><span>提醒</span><strong>暂无</strong></div>";
    }
  }

  function renderHourly(hourly) {
    var list = byId("hourly-list");
    if (list) {
      var html = "";
      var i;
      for (i = 0; i < hourly.length && i < 12; i += 1) {
        html += "<div class=\"hourly-row\"><span>" + escapeHtml(hourly[i].time || "--") + "</span><b>" + escapeHtml(shortCondition(hourly[i].condition || "--")) + "</b><em>" + Math.round(Number(hourly[i].temperature || 0)) + "°</em><i>" + pct(hourly[i].rain) + "%</i></div>";
      }
      list.innerHTML = html || "<div class=\"hourly-row\"><span>--</span><b>暂无</b><em>--</em><i>降水--</i></div>";
    }
  }

  function formatDailyTrend(items) {
    if (!items || !items.length) {
      return "三日趋势 --";
    }
    var parts = [];
    var i;
    for (i = 1; i < items.length && parts.length < 2; i += 1) {
      parts.push((items[i].day || "--") + " " + Math.round(Number(items[i].high || 0)) + "/" + Math.round(Number(items[i].low || 0)) + " " + (items[i].condition || "--"));
    }
    return "三日趋势 " + parts.join(" · ");
  }

  function shortCondition(value) {
    return String(value).replace("小毛毛雨", "小雨").replace("毛毛雨", "小雨").replace("大毛毛雨", "大雨");
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (c) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"}[c];
    });
  }

  function loadLatest() {
    if (!window.XMLHttpRequest) {
      return;
    }
    try {
      var xhr = new XMLHttpRequest();
      xhr.open("GET", "data/latest.json?ts=" + new Date().getTime(), true);
      xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status >= 200 && xhr.status < 300) {
          try {
            render(JSON.parse(xhr.responseText));
          } catch (ignore) {}
        }
      };
      xhr.send(null);
    } catch (ignore) {}
  }

  updateClock();
  render(data);
  loadLatest();
  window.setInterval(updateClock, 30000);
  window.setInterval(function () {
    window.location.reload(true);
  }, 1800000);
}());
