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
    var almanac = data.almanac || {};
    var outing = data.outing || {};
    var scores = outing.scores || {};
    var weather = data.weather || {};
    var sun = data.sun || {};
    var hot = data.hotsearch || [];

    text("city", data.city || "杭州");
    text("updated", data.generated_at ? "更新 " + String(data.generated_at).replace("T", " ").slice(5, 16) : "离线预览");
    text("status", data.stale ? "数据较旧" : "数据正常");
    text("solar", date.solar);
    text("weekday", date.weekday);
    text("lunar", date.lunar);
    text("ganzhi", date.ganzhi);
    text("yi", joinList(almanac.yi));
    text("ji", joinList(almanac.ji));
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

    text("sunrise", shortTime(sun.sunrise));
    text("sunset", shortTime(sun.sunset));
    text("daylight", sun.daylight ? "白昼 " + sun.daylight : "白昼 --");

    var list = byId("hotlist");
    if (list) {
      var html = "";
      var i;
      for (i = 0; i < hot.length && i < 6; i += 1) {
        html += "<li><span>" + (hot[i].rank || i + 1) + "</span><b>" + escapeHtml(hot[i].title || "--") + "</b></li>";
      }
      list.innerHTML = html || "<li><span>1</span><b>暂无热搜</b></li>";
    }
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
