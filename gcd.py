import datetime
import os

from exporter import Exporter
from google.cloud import datastore

class GoogleCloudDatastoreExporter(Exporter):
    def __init__(self, project, namespace):
        self._client = datastore.Client(project=project, namespace=namespace)
    
    def name(self):
        return "Google Cloud Datastore"
    
    def export(self, measurements, ts=None):
        if ts is None:
            ts = datetime.datetime.utcnow()
        entities = []
        for mac, content in measurements:
            key = self._client.key("Measurement")
            e = datastore.Entity(key=key, exclude_from_indexes=("temperature", "humidity", "pressure"))
            e["mac"] = mac
            e["name"] = content["name"]
            e["ts"] = ts
            e["temperature"] = float(content["temperature"])
            e["humidity"] = float(content["humidity"])
            e["pressure"] = float(content["pressure"])
            entities.append(e)
        self._client.put_multi(entities)
    
    def close(self):
        pass