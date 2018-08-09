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

RUUVITAG_USE_SQLITE=1
RUUVITAG_SQLITE_FILE=/path/to/database/file.db

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

from gcd import GoogleCloudDatastoreExporter
from sqlite import SQLiteExporter
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.decoder import get_decoder
from influx import InfluxDBExporter
from ruuvicfg import get_ruuvitags

ini_file = os.environ.get("RUUVITAG_CONFIG_FILE", "ruuvitags.ini")

tags = get_ruuvitags(inifile=ini_file)
if not tags:
	print("No RuuviTag definitions found from configuration file " + ini_file)
	quit(1)

exporters = []
if os.environ.get("RUUVITAG_USE_SQLITE", "0") == "1":
	exporters.append(lambda: SQLiteExporter(os.environ.get("RUUVITAG_SQLITE_FILE", "ruuvitag.db")))
if os.environ.get("RUUVITAG_USE_INFLUXDB", "0") == "1":
	exporters.append(lambda: InfluxDBExporter())
if os.environ.get("RUUVITAG_USE_GCD", "0") == "1":
	gcd_project = os.environ.get("RUUVITAG_GCD_PROJECT")
	gcd_namespace = os.environ.get("RUUVITAG_GCD_NAMESPACE")
	exporters.append(lambda: GoogleCloudDatastoreExporter(gcd_project, gcd_namespace))
# Add your own exporters here

ts = datetime.datetime.utcnow()
db_data = {}

print("Reading measurements from RuuviTags " + str(tags))
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

for create_exporter in exporters:
	with create_exporter() as exporter:
		print("Saving data to {}...".format(exporter.name()))
		exporter.export(db_data.items(), ts)

print("Done.")
