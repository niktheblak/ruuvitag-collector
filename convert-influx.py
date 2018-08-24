import datetime
import influx
import logging
import os

from exporter import Exporter
from influxdb import InfluxDBClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('convert-influx')

cfg = influx.InfluxDBConfig()
logging.info('Using InfluxDB config %s', cfg)
client = InfluxDBClient(
    host=cfg.host,
    port=cfg.port,
    username=cfg.username,
    password=cfg.password,
    database=cfg.database,
    ssl=cfg.ssl,
    verify_ssl=cfg.ssl,
    path=cfg.path
)

batch_size = 100
offset = 0

while True:
    logger.debug('Querying measurements: %d-%d', offset, offset + batch_size)
    results = client.query('SELECT * FROM "temperature", "humidity", "pressure" ORDER BY "time" LIMIT {} OFFSET {}'.format(batch_size, offset))
    if not results:
        break
    logger.debug('Read measurements: %s', results)
    measurements = []
    for row in results['temperature']:
        m = row.copy()
        m['temperature'] = m['value']
        m.pop('value', None)
        measurements.append(m)
    i = 0
    for row in results['humidity']:
        measurements[i]['humidity'] = row['value']
        i += 1
    i = 0
    for row in results['pressure']:
        measurements[i]['pressure'] = row['value']
        i += 1
    logger.debug('Collected measurements: %s', measurements)
    logger.info('Writing measurements %d-%d', offset, offset + len(measurements))
    points = []
    for measurement in measurements:
        point = {
            'measurement': 'ruuvitag_sensor',
            'tags': {
                'name': measurement['ruuvitag'],
                'mac': measurement['mac']
            },
            'time': measurement['time'],
            'fields': {
                'temperature': measurement['temperature'],
                'humidity': measurement['humidity'],
                'pressure': measurement['pressure']
            }
        }
        points.append(point)
    client.write_points(points)
    if len(measurements) != batch_size:
        # We've reached the last batch
        break
    offset += len(measurements)
