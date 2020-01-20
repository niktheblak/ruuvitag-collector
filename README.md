# ruuvitag-collector
Collects data from RuuviTag sensors to SQLite, InfluxDB and other databases.

Based on https://github.com/kuosman/RuuviTag-logger but modified heavily
for my (and hopefully others') use case.

## Used elements
  - [Raspberry Pi 3](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/)
  - [Python 3](https://docs.python.org/3.7/)
  - [RuuviTag Sensor Python Package](https://github.com/ttu/ruuvitag-sensor)
  - [SQLite 3 database](https://docs.python.org/3.6/library/sqlite3.html#module-sqlite3)

## Setup

Copy the file `example-config.yaml` to `$HOME/.config/ruuvitag-collector/config.yaml`.

Add the MAC addresses and human-readable names of your RuuviTags into the config file
under the `ruuvitags` key:

```yaml
ruuvitags:
  "CC:CA:7E:52:CC:34": Backyard
  "FB:E1:B7:04:95:EE": Upstairs
  "E8:E0:C6:0B:B8:C5": Downstairs
```

If you want to save data to local SQLite database, add the following options to your config file:

```yaml
sqlite:
  enabled: true
  file: /home/pi/ruuvitag/ruuvitag.db
```

If you want to save data to InfluxDB (local or remote), add the following options to your config file:

```yaml
influxdb:
  enabled: true
  host: localhost
  port: 8086
  database: ruuvitag
  measurement: ruuvitag
  username: root
  password: root
```

Now you can try to run it manually:

```bash
$ ./ruuvitag-logger.py
OR
$ /home/pi/ruuvitag/ruuvitag-logger.py
OR
$ python3 ruuvitag-logger.py
```

Set crontab to run logger automatically every 30 mins:
```bash
Add this line to the /etc/crontab file

*/30 *  * * *   pi      /home/pi/ruuvitag/ruuvitag-logger.py > /home/pi/ruuvitag/ruuvitag.log 2> /home/pi/ruuvitag/ruuvitag.err
```
Cron will output success log to `ruuvitag.log` file and errors to `ruuvitag.err` file.
