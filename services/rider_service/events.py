import redis
import json

from datetime import datetime

r = redis.Redis(
    host = "local",
    port = 6379,
    decode_responses = True
)

def publish_event(event_name: str, data: dict):
    data["timestep"] = datetime.now()

    payload = json.dumps(data)

    r.publish(
        event_name,
        payload
    )
    print(f"Event fired: {event_name} → {data}")

def event_rider_registered(rider_id: int, payment_method: str):
    publish_event(
        "rider.registered",
        {
            rider_id: rider_id,
            payment_method: payment_method
        }
    )