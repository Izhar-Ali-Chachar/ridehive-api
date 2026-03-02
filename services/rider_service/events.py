import redis
import json

from datetime import datetime

import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

def publish_event(event_name: str, data: dict):
    data["timestamp"] = datetime.now().isoformat()

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
            "rider_id": rider_id,
            "payment_method": payment_method
        }
    )

def event_ride_requested(
    ride_id: int,
    rider_id: int,
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float,
    estimated_fare: float
):
    publish_event(
        "ride.requested",
        {
            "ride_id": ride_id,
            "rider_id": rider_id,
            "pickup_lat": pickup_lat,
            "pickup_lng": pickup_lng,
            "dropoff_lat": dropoff_lat,
            "dropoff_lng": dropoff_lng,
            "estimated_fare": estimated_fare
        }
    )

def event_ride_cancelled(
        ride_id: int,
        rider_id: int,
        reason: str
):
    publish_event(
        "ride.cancelled",
        {
            "ride_id": ride_id,
            "rider_id": rider_id,
            "reason": reason
        }
    )