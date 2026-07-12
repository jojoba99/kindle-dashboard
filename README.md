# Kindle 信息屏

适配 Kindle Paperwhite 一代实验浏览器的黑白静态信息屏。页面显示时间日期、今日提醒、今日出门、天气、日出日落、三日趋势和未来 12 小时预报。

## 本地预览

```bash
python3 -m http.server 8000
```

打开 `http://localhost:8000/` 即可预览。

## 更新数据

```bash
python3 scripts/update_data.py
```

脚本会生成 `data/latest.json`，并把同一份数据预渲染进 `index.html`。脚本只使用 Python 标准库。

## 自动发布

`.github/workflows/update-kindle-dashboard.yml` 会每 45 分钟运行一次，生成数据并部署到 GitHub Pages。Kindle 只需要打开 Pages 地址，保持 Wi-Fi 可用；未越狱设备无法被网页从休眠中主动唤醒。

## 默认配置

- 城市：杭州
- 天气：Open-Meteo
- 今日提醒：由天气数据本地计算
