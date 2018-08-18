import datetime
import json

from google.cloud import pubsub_v1
from exporter import Exporter

class GooglePubSubExporter(Exporter):
    def __init__(self, project, topic_name):
        self._publisher = pubsub_v1.PublisherClient()
        self._topic_path = self._publisher.topic_path(project, topic_name)
    
    def name(self):
        return "Google Pub/Sub"

    def close(self):
        pass

    def export(self, measurements, ts=None):
        if ts is None:
            ts = datetime.datetime.utcnow()
        for mac, content in measurements:
            m = {}
            m["mac"] = mac
            m["name"] = content["name"]
            m["ts"] = ts.replace(tzinfo=datetime.timezone.utc).isoformat()
            m["temperature"] = float(content["temperature"])
            m["humidity"] = float(content["humidity"])
            m["pressure"] = float(content["pressure"])
            data = json.dumps(m).encode("utf-8")
            self._publisher.publish(self._topic_path, data, mac=mac, name=content["name"])
