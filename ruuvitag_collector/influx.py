import datetime

from ruuvitag_collector.exporter import Exporter
from influxdb import InfluxDBClient


class InfluxDBExporter(Exporter):
    def __init__(self, config):
        cfg = InfluxDBConfig(config)
        self._measurement = cfg.measurement
        self._client = InfluxDBClient(
            host=cfg.host,
            port=cfg.port,
            username=cfg.username,
            password=cfg.password,
            database=cfg.database,
            ssl=cfg.ssl,
            verify_ssl=cfg.ssl,
            path=cfg.path
        )

    def name(self):
        return "InfluxDB"

    def export(self, measurements, ts=None):
        if ts is None:
            ts = datetime.datetime.utcnow()
        for mac, content in measurements:
            points = self._to_influx_points(ts, mac, content)
            self._client.write_points(points)

    def close(self):
        self._client.close()

    def _to_influx_points(self, ts, mac, content):
        return [
            {
                "measurement": self._measurement,
                "tags": {
                    "name": content["name"],
                    "mac": mac
                },
                "time": ts.isoformat(),
                "fields": {
                    "temperature": float(content["temperature"]),
                    "humidity": float(content["humidity"]),
                    "pressure": float(content["pressure"])
                }
            }
        ]


class InfluxDBConfig:
    def __init__(self, cfg):
        influxdb_cfg = cfg['influxdb']
        self.ssl = influxdb_cfg['ssl'].get(False)
        self.host = influxdb_cfg['host'].get('localhost')
        self.port = influxdb_cfg['port'].get(8086)
        self.database = influxdb_cfg['database'].get('ruuvitag')
        self.measurement = influxdb_cfg['measurement'].get('ruuvitag_sensor')
        self.username = influxdb_cfg['username'].get('root')
        self.password = influxdb_cfg['password'].get('root')
        self.path = influxdb_cfg['path'].get('')
