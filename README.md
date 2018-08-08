# RuuviTag-logger
Log RuuviTags data to SQLite or InfluxDB database.

Based on https://github.com/kuosman/RuuviTag-logger but modified heavily
for my (and hopefully others') use case.

## Used elements
  - [Raspberry Pi 3](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/)
  - [Python 3](https://docs.python.org/3.6/)
  - [RuuviTag Sensor Python Package](https://github.com/ttu/ruuvitag-sensor) by [Tomi Tuhkanen](https://github.com/ttu)
  - [SQLite 3 database](https://docs.python.org/3.6/library/sqlite3.html#module-sqlite3)

## Setup

Create an ini file that contains MAC addresses and human-readable names of your
RuuviTags:

```
[DEFAULT]
CC:CA:7E:52:CC:34 = Backyard
FB:E1:B7:04:95:EE = Upstairs
E8:E0:C6:0B:B8:C5 = Downstairs
```

Declare the ini file location in the environment variable:

```bash
export RUUVITAG_CONFIG_FILE=/home/pi/ruuvitag/ruuvitags.ini
```

If you want to save data to local SQLite database, set the following environment variables:

```bash
export RUUVITAG_USE_SQLITE=1
export RUUVITAG_SQLITE_FILE=/home/pi/ruuvitag/ruuvitag.db
```

If you want to save data to InfluxDB (local or remote), set the following environment variables:

```bash
export RUUVITAG_USE_INFLUXDB=1
export RUUVITAG_INFLUXDB_HOST=localhost
export RUUVITAG_INFLUXDB_PORT=8086
export RUUVITAG_INFLUXDB_DATABASE=ruuvitag
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
