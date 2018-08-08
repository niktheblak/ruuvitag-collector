#!/usr/bin/python3

"""
Imports data from local SQLite database to InfluxDB.
"""

import argparse
import datetime
import sqlite3
import os

from influx import InfluxDBConfig, to_influx_points
from influxdb import InfluxDBClient

parser = argparse.ArgumentParser(description='Import data from local SQLite database to InfluxDB.')
parser.add_argument("-f", "--file", dest="db_file", help="path to SQLite database file")
parser.add_argument("--host", dest="host", help="InfluxDB host")
parser.add_argument("--port", dest="port", help="InfluxDB port")
parser.add_argument("--username", dest="username", help="InfluxDB username")
parser.add_argument("--password", dest="password", help="InfluxDB password")
parser.add_argument("--database", dest="database", help="InfluxDB database")
parser.add_argument("--ssl", dest="ssl", help="use SSL for InfluxDB", action='store_true')
args = parser.parse_args()

db_file = os.environ.get("RUUVITAG_LOCAL_DB_FILE", "ruuvitag.db")
if args.db_file:
    db_file = args.db_file
conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)

influxdb_cfg = InfluxDBConfig()
if args.host:
    influxdb_cfg.host = args.host
if args.port:
    influxdb_cfg.port = args.port
if args.username:
    influxdb_cfg.username = args.username
if args.password:
    influxdb_cfg.password = args.password
if args.database:
    influxdb_cfg.database = args.database
if args.ssl:
    influxdb_cfg.ssl = args.ssl
influxdb_client = InfluxDBClient(
    host=influxdb_cfg.host,
    port=influxdb_cfg.port,
    username=influxdb_cfg.username,
    password=influxdb_cfg.password,
    database=influxdb_cfg.database,
    ssl=influxdb_cfg.ssl,
    verify_ssl=influxdb_cfg.ssl
)

i = 1
rows = conn.execute("SELECT id, timestamp, mac, name, temperature, humidity, pressure FROM sensors")
print("Starting import...")
for row in rows:
    ts = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f")
    mac = row[2]
    content = {
        "ts": ts,
        "name": row[3],
        "temperature": float(row[4]),
        "humidity": float(row[5]),
        "pressure": float(row[6])
    }
    points = to_influx_points(None, mac, content)
    influxdb_client.write_points(points)
    if i % 100 == 0:
        print("Imported {} rows".format(i))
    i += 1

print("Imported {} rows.".format(i))
print("Import done.")

conn.close()
influxdb_client.close()
