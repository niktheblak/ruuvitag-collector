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
import logging
import os
import sys

from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.decoder import get_decoder
from ruuvicfg import get_ruuvitags

if os.environ.get("RUUVITAG_USE_STACKDRIVER", "0") == "1":
    import google.cloud.logging
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
else:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ruuvitag-collector")

ini_file = os.environ.get("RUUVITAG_CONFIG_FILE", "ruuvitags.ini")

tags = get_ruuvitags(inifile=ini_file)
if not tags:
    logger.critical(
        "No RuuviTag definitions found from configuration file %s", ini_file)
    quit(1)

exporters = []
if os.environ.get("RUUVITAG_USE_SQLITE", "0") == "1":
    logger.info("Using SQLite exporter")
    from sqlite import SQLiteExporter
    exporters.append(lambda: SQLiteExporter(
        os.environ.get("RUUVITAG_SQLITE_FILE", "ruuvitag.db")))
if os.environ.get("RUUVITAG_USE_INFLUXDB", "0") == "1":
    logger.info("Using InfuxDB exporter")
    from influx import InfluxDBExporter
    exporters.append(lambda: InfluxDBExporter())
if os.environ.get("RUUVITAG_USE_GCD", "0") == "1":
    logger.info("Using Google Cloud Datastore exporter")
    from gcd import GoogleCloudDatastoreExporter
    gcd_project = os.environ.get("RUUVITAG_GCD_PROJECT")
    gcd_namespace = os.environ.get("RUUVITAG_GCD_NAMESPACE")
    exporters.append(lambda: GoogleCloudDatastoreExporter(
        gcd_project, gcd_namespace))
if os.environ.get("RUUVITAG_USE_PUBSUB", "0") == "1":
    logger.info("Using Google Pub/Sub exporter")
    from pubsub import GooglePubSubExporter
    pubsub_project = os.environ.get("RUUVITAG_PUBSUB_PROJECT")
    pubsub_topic = os.environ.get("RUUVITAG_PUBSUB_TOPIC")
    exporters.append(lambda: GooglePubSubExporter(
        pubsub_project, pubsub_topic))
# Add your own exporters here

ts = datetime.datetime.utcnow()
db_data = {}

for mac, name in tags.items():
    logger.info("Reading measurements from RuuviTag %s (%s)...", name, mac)
    encoded = RuuviTagSensor.get_data(mac)
    decoder = get_decoder(encoded[0])
    data = decoder.decode_data(encoded[1])
    logger.debug("Data received: %s", data)

    db_data[mac] = {"name": name}
    # add each sensor with value to the lists
    for sensor, value in data.items():
        db_data[mac].update({sensor: value})

for create_exporter in exporters:
    with create_exporter() as exporter:
        logger.info("Exporting data to %s", exporter.name())
        try:
            exporter.export(db_data.items(), ts)
        except Exception as e:
            logger.error("Error while exporting data to %s: %s", exporter.name(), e)

logger.info("Done.")
