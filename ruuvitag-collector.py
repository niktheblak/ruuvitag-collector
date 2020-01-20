#!/usr/bin/env python3

"""
Reads measurements from RuuviTag sensors and stores them to a local SQLite
database and/or InfluxDB.

The RuuviTag sensor MAC addresses and human-friendly names must be listed in
ruuvitags.yaml file with MAC-name pairs under the ruuvitags collection.
Example yaml file content:

ruuvitags:
  "CC:CA:7E:52:CC:34": "Backyard"
  "FB:E1:B7:04:95:EE": "Upstairs"
  "E8:E0:C6:0B:B8:C5": "Downstairs"

Declare the ini file location in the environment variable:

RUUVITAG_CONFIG_FILE=/path/to/ruuvitags.yaml

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

from retrying import retry
from ruuvitag_sensor.decoder import get_decoder
from ruuvitag_sensor.ruuvi import RuuviTagSensor

from ruuvicfg import get_ruuvitags


def create_exporters():
    exporters = []
    if os.environ.get("RUUVITAG_USE_SQLITE", "0") == "1":
        from sqlite import SQLiteExporter
        exporters.append(lambda: SQLiteExporter(
            os.environ.get("RUUVITAG_SQLITE_FILE", "ruuvitag.db")))
    if os.environ.get("RUUVITAG_USE_INFLUXDB", "0") == "1":
        from influx import InfluxDBExporter
        exporters.append(lambda: InfluxDBExporter())
    if os.environ.get("RUUVITAG_USE_GCD", "0") == "1":
        from gcd import GoogleCloudDatastoreExporter
        gcd_project = os.environ.get("RUUVITAG_GCD_PROJECT")
        gcd_namespace = os.environ.get("RUUVITAG_GCD_NAMESPACE")
        exporters.append(lambda: GoogleCloudDatastoreExporter(
            gcd_project, gcd_namespace))
    if os.environ.get("RUUVITAG_USE_PUBSUB", "0") == "1":
        from pubsub import GooglePubSubExporter
        pubsub_project = os.environ.get("RUUVITAG_PUBSUB_PROJECT")
        pubsub_topic = os.environ.get("RUUVITAG_PUBSUB_TOPIC")
        exporters.append(lambda: GooglePubSubExporter(
            pubsub_project, pubsub_topic))
    # Your exporters here
    return exporters


def collect_measurements(items):
    measurements = {}
    for mac, name in items:
        logger.info("Reading measurements from RuuviTag %s (%s)", name, mac)
        encoded = RuuviTagSensor.get_data(mac)
        decoder = get_decoder(encoded[0])
        data = decoder.decode_data(encoded[1])
        logger.debug("Data received: %s", data)

        measurements[mac] = {"name": name}
        for sensor, value in data.items():
            measurements[mac].update({sensor: value})
    return measurements


if os.environ.get("RUUVITAG_USE_STACKDRIVER_LOGGING", "0") == "1":
    import google.cloud.logging

    logging_client = google.cloud.logging.Client()
    handler = logging_client.get_default_handler()
    logger = logging.getLogger("ruuvitag-collector")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
else:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ruuvitag-collector")

cfg_file = os.environ.get("RUUVITAG_CONFIG_FILE", "ruuvitags.yaml")
tags = {}
try:
    tags = get_ruuvitags(cfg_file=cfg_file)
except Exception as exc:
    logger.critical("Failed to read RuuviTag configuration file", exc)
    quit(1)
if not tags:
    logger.critical(
        "No RuuviTag definitions found from configuration file %s", cfg_file)
    quit(1)

exporters = create_exporters()
ts = datetime.datetime.utcnow()
meas = collect_measurements(tags.items())


@retry(stop_max_attempt_number=10, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def export(exp, items):
    exp.export(items, ts)


for create_exporter in exporters:
    with create_exporter() as exporter:
        logger.info("Exporting data to %s", exporter.name())
        try:
            export(exporter, meas.items())
        except Exception as e:
            logger.error("Error while exporting data to %s: %s",
                         exporter.name(), e)

logger.info("Done")
