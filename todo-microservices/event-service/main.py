from fastapi import FastAPI
from kafka_producer import send_event
from mongodb_client import events_collection
import datetime

app = FastAPI()


@app.post("/event")
def handle_event(event: dict):
    print("Event received:", event)

    # Сохраняем в MongoDB
    event_record = {
        "event": event,
        "received_at": datetime.datetime.utcnow(),
        "source": "task-service"
    }
    events_collection.insert_one(event_record)

    # Отправляем в Kafka
    send_event(event)

    return {"status": "sent to kafka"}