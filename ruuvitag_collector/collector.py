"""
Reads measurements from RuuviTag sensors and stores them to a local SQLite
database and/or InfluxDB.

The RuuviTag sensor MAC addresses and human-friendly names must be listed in
$HOME/.config/ruuvitag-collector/config.yaml file with MAC-name pairs under
the ruuvitags key. Example yaml file content:

ruuvitags:
  "CC:CA:7E:52:CC:34": Backyard
  "FB:E1:B7:04:95:EE": Upstairs
  "E8:E0:C6:0B:B8:C5": Downstairs

If you want to store measurement data to e.g. local SQLite database, add the
following keys to your config.yaml:

sqlite:
  enabled: true
  file: /path/to/database/file.db

For other storage options, look up the configuration options from README.md.
"""

import datetime
import logging

from ruuvitag_sensor.decoder import get_decoder
from ruuvitag_sensor.ruuvi import RuuviTagSensor


logger = logging.getLogger("ruuvitag-collector")


def create_exporters(config):
    exporters = []
    if config['sqlite']['enabled'].get(False):
        from ruuvitag_collector.sqlite import SQLiteExporter
        exporters.append(lambda: SQLiteExporter(
            config['sqlite']['file'].as_filename()))
    if config['influxdb']['enabled'].get(False):
        from ruuvitag_collector.influx import InfluxDBExporter
        exporters.append(lambda: InfluxDBExporter(config))
    if config['gcd']['enabled'].get(False):
        from ruuvitag_collector.gcd import GoogleCloudDatastoreExporter
        gcd_project = config['gcd']['project'].get(str)
        gcd_namespace = config['gcd']['namespace'].get(str)
        exporters.append(lambda: GoogleCloudDatastoreExporter(
            gcd_project, gcd_namespace))
    if config['pubsub']['enabled'].get(False):
        from ruuvitag_collector.pubsub import GooglePubSubExporter
        pubsub_project = config['pubsub']['project'].get(str)
        pubsub_topic = config['pubsub']['topic'].get(str)
        exporters.append(lambda: GooglePubSubExporter(
            pubsub_project, pubsub_topic))
    # Your exporters here
    return exporters


def collect_measurements(ruuvitags):
    measurements = dict()
    for mac, name in ruuvitags.items():
        logger.info("Reading measurements from RuuviTag %s (%s)", name, mac)
        (data_format, encoded) = RuuviTagSensor.get_data(mac)
        if data_format is None or encoded is None:
            logger.warning("Invalid data from RuuviTag %s", name)
            continue
        decoder = get_decoder(data_format)
        data = decoder.decode_data(encoded)
        logger.debug("Data received: %s", data)
        data["name"] = name
        measurements[mac] = data
    return measurements
