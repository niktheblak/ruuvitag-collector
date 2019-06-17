import datetime
import json

from google.cloud import pubsub_v1
from exporter import Exporter


class GooglePubSubExporter(Exporter):
    def __init__(self, project, topic_name):
        if not project:
            raise Exception("Pub/Sub project ID must be specified")
        if not topic_name:
            raise Exception("Pub/Sub topic must be specified")
        self._publisher = pubsub_v1.PublisherClient()
        self._topic_path = self._publisher.topic_path(project, topic_name)

    def name(self):
        return "Google Pub/Sub"

    def close(self):
        pass

    def export(self, measurements, ts=None):
        if ts is None:
            ts = datetime.datetime.utcnow()
        futures = []
        for mac, content in measurements:
            m = {
                "mac": mac,
                "name": content["name"],
                "ts": ts.isoformat(),
                "temperature": float(content["temperature"]),
                "humidity": float(content["humidity"]),
                "pressure": float(content["pressure"])
            }
            data = json.dumps(m).encode("utf-8")
            message_future = self._publisher.publish(
                self._topic_path, data, mac=mac, name=content["name"])
            futures.append(message_future)
        for future in futures:
            future.result(timeout=10)
