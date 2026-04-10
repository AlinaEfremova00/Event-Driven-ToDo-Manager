from kafka import KafkaProducer
import json
import os

KAFKA_HOST = os.getenv("KAFKA_HOST", "localhost")

producer = None

def get_producer():
    global producer
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers=f'{KAFKA_HOST}:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    return producer

def send_event(event):
    print("Sending event to Kafka:", event)
    p = get_producer()
    p.send('tasks', event)