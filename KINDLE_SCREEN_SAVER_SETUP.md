# Kindle screensaver update setup

This project already supports the installed `linkss` screensaver hack by writing:

```text
/mnt/us/linkss/screensavers/bg_medium_ss00.png
```

## Synology side

Run this in DSM Task Scheduler every 45-60 minutes:

```sh
/bin/sh /volume1/web/kindle-dashboard/scripts/synology_update_screensaver.sh
```

It generates:

```text
http://172.22.22.116/kindle-dashboard/screensaver/kindle-dashboard.png
```

The renderer requires Python 3 and Pillow.

## Kindle side

Copy `kindle/bin/update_screensaver.sh` to:

```text
/mnt/us/extensions/kindle-dashboard/bin/update_screensaver.sh
```

Copy `kindle/extensions/kindle-dashboard/menu.json` to:

```text
/mnt/us/extensions/kindle-dashboard/menu.json
```

With KUAL installed, run:

```text
Update dashboard screensaver
```

For automatic periodic refresh on the Kindle, install USBNetwork or another startup/cron-capable package, then run:

```sh
/mnt/us/extensions/kindle-dashboard/bin/update_screensaver.sh
```

on a schedule.
