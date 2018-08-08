import datetime
import os

from influxdb import InfluxDBClient

class InfluxDBConfig:
    def __init__(self):
        self.enabled = os.environ.get("RUUVITAG_USE_INFLUXDB", "0") == "1"
        self.ssl = os.environ.get("RUUVITAG_INFLUXDB_SSL", "0") == "1"
        self.host = os.environ.get("RUUVITAG_INFLUXDB_HOST", "localhost")
        self.port = int(os.environ.get("RUUVITAG_INFLUXDB_PORT", "8086"))
        self.database = os.environ.get("RUUVITAG_INFLUXDB_DATABASE")
        self.username = os.environ.get("RUUVITAG_INFLUXDB_USERNAME", "root")
        self.password = os.environ.get("RUUVITAG_INFLUXDB_PASSWORD", "root")

def to_influx_points(ts, mac, content):
    if "ts" in content:
        ts_from_content = content["ts"]
        if isinstance(ts_from_content, datetime.datetime):
            ts = ts_from_content
    isots = ts.replace(microsecond=0).replace(tzinfo=datetime.timezone.utc).isoformat()
    return [
        {
            "measurement": "temperature",
            "tags": {
                "ruuvitag": content["name"],
                "mac": mac
            },
            "time": isots,
            "fields": {
                "value": content["temperature"]
            }
        },
        {
            "measurement": "humidity",
            "tags": {
                "ruuvitag": content["name"],
                "mac": mac
            },
            "time": isots,
            "fields": {
                "value": content["humidity"]
            }
        },
        {
            "measurement": "pressure",
            "tags": {
                "ruuvitag": content["name"],
                "mac": mac
            },
            "time": isots,
            "fields": {
                "value": content["pressure"]
            }
        }
    ]
