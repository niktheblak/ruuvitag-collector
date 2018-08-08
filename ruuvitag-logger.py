#!/usr/bin/python3

"""
Reads measurements from RuuviTag sensors and stores them to a local SQLite
database and/or InfluxDB.

The RuuviTag sensor MAC addresses and human-friendly names must be listed in
ruuvitags.ini file with one MAC=Name pair in each line. Example ini file content:

[DEFAULT]
C7:10:31:99:61:E2 = Living room
D3:B2:9F:90:4B:0A = Bedroom
F8:36:EC:93:BD:59 = Bathroom

Declare the ini file location in the environment variable:

RUUVITAG_CONFIG_FILE=/path/to/ruuvitags.ini

If you want to store measurement data to a local SQLite database, set
the following environment variables:

RUUVITAG_USE_LOCAL_DB=1
RUUVITAG_LOCAL_DB_FILE=/path/to/database/file.db

If you want to store measurement data to InfluxDB (local or remote), set at least the
following environment variables:

RUUVITAG_USE_INFLUXDB=1
RUUVITAG_INFLUXDB_HOST=localhost
RUUVITAG_INFLUXDB_DATABASE=ruuvitag

If you need to use nonstandard options for port, SSL, username etc., look up the
environment variable names from influx.py.
"""

import datetime
import os

from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.decoder import get_decoder
from influx import InfluxDBConfig, to_influx_points
from ruuvicfg import get_ruuvitags

ini_file = os.environ.get("RUUVITAG_CONFIG_FILE", "ruuvitags.ini")

tags = get_ruuvitags(inifile=ini_file)
if not tags:
	print("No RuuviTag definitions found from configuration file " + ini_file)
	quit(1)
print("Reading measurements from RuuviTags " + str(tags))

local_db = os.environ.get("RUUVITAG_USE_LOCAL_DB", "0") == "1"
local_db_file = os.environ.get("RUUVITAG_LOCAL_DB_FILE", "ruuvitag.db")

influxdb_cfg = InfluxDBConfig()

if local_db:
	import sqlite3
	# open database
	conn = sqlite3.connect(local_db_file)

	# check if table exists
	cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sensors'")
	row = cursor.fetchone()
	if row is None:
		print("Creating local database table")
		conn.execute('''CREATE TABLE sensors (
				id				INTEGER		PRIMARY KEY AUTOINCREMENT NOT NULL,
				timestamp		DATETIME	DEFAULT CURRENT_TIMESTAMP,
				mac				TEXT		NOT NULL,
				name			TEXT,
				temperature		REAL,
				humidity		REAL,
				pressure		REAL
			);''')
		print("Table created successfully")

if influxdb_cfg.enabled:
	import influx
	from influxdb import InfluxDBClient

	influxdb_client = InfluxDBClient(
		host=influxdb_cfg.host,
		port=influxdb_cfg.port,
		username=influxdb_cfg.username,
		password=influxdb_cfg.password,
		database=influxdb_cfg.database,
		ssl=influxdb_cfg.ssl,
		verify_ssl=influxdb_cfg.ssl
	)

ts = datetime.datetime.utcnow()

db_data = {}

for mac, name in tags.items():
	print("Reading measurements from RuuviTag {} ({})...".format(name, mac))
	encoded = RuuviTagSensor.get_data(mac)
	decoder = get_decoder(encoded[0])
	data = decoder.decode_data(encoded[1])
	print("Data received: {}".format(data))

	db_data[mac] = {"name": name}
	# add each sensor with value to the lists
	for sensor, value in data.items():
		db_data[mac].update({sensor: value})

if local_db:
	print("Saving data to local database...")
	for mac, content in db_data.items():
		conn.execute('''INSERT INTO sensors
			(timestamp, mac, name, temperature, humidity, pressure)
			VALUES (?, ?, ?, ?, ?, ?)''',
			(ts, mac, content['name'], content['temperature'], content['humidity'], content['pressure']))
	conn.commit()
	conn.close()

if influxdb_cfg.enabled:
	print("Saving data to InfluxDB...")
	for mac, content in db_data.items():
		points = to_influx_points(ts, mac, content)
		influxdb_client.write_points(points)

print("Done.")
