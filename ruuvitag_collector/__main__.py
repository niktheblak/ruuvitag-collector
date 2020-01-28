from ruuvitag_collector.collector import create_exporters, collect_measurements
import datetime
import logging

import confuse
from retrying import retry


config = confuse.Configuration('ruuvitag-collector', __name__)
if config['stackdriver']['enabled'].get(False):
    import google.cloud.logging
    logging_client = google.cloud.logging.Client()
    handler = logging_client.get_default_handler()
    logger = logging.getLogger("ruuvitag-collector")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
else:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ruuvitag-collector")
tags = config['ruuvitags'].as_pairs()
if not tags:
    logger.critical(
        "No RuuviTag definitions found from configuration")
    quit(1)

exporters = create_exporters(config)
ts = datetime.datetime.utcnow()
names = dict(tags)
measurements = collect_measurements(names)
if not measurements:
    logger.warning("No measurements could be read")
    quit()


@retry(stop_max_attempt_number=10,
       wait_exponential_multiplier=1000, wait_exponential_max=10000)
def export(exp, items):
    exp.export(items, ts)


for create_exporter in exporters:
    with create_exporter() as exporter:
        logger.info("Exporting data to %s", exporter.name())
        try:
            export(exporter, measurements.items())
        except Exception as e:
            logger.error("Error while exporting data to %s: %s",
                         exporter.name(), e)

logger.info("Done")
