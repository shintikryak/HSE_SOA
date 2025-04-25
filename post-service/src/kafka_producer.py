import os, json
from confluent_kafka import Producer

_bootstrap = "kafka:9092"
_producer  = Producer({"bootstrap.servers": _bootstrap})

def publish(topic: str, event: dict):
    _producer.produce(topic, json.dumps(event).encode("utf-8"))
    _producer.flush()
