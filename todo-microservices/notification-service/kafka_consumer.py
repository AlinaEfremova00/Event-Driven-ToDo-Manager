from kafka import KafkaConsumer
import json
import os

KAFKA_HOST = os.getenv("KAFKA_HOST", "localhost")

def safe_deserialize(x):
    try:
        return json.loads(x.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"Skipping invalid JSON message: {x}")
        return None

consumer = KafkaConsumer(
    'tasks',
    bootstrap_servers=f'{KAFKA_HOST}:9092',
    value_deserializer=safe_deserialize,
    auto_offset_reset='earliest',
    group_id='notification-group'
)

def start_consumer():
    print("Kafka consumer started...")
    for message in consumer:
        event = message.value
        if event is not None:
            print("Received event from Kafka:", event)
        else:
            print("Skipped invalid message")