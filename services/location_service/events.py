import redis.asyncio as redis
import json
from datetime import datetime

from services.location_service.cache import (
    add_online_driver,
    remove_online_driver,
    delete_driver_location
)


r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

def publish_event(event_name: str, data: dict):
    data["timestamp"] = datetime.now().isoformat()

    payload = json.dumps(data)

    r.publish(
        event_name,
        payload
    )

    print(f"event publish with {event_name} and {data}")

def event_location_updated(
        driver_id: int,
        latitude: float,
        longitude: float,
        ride_id: int
):
    publish_event(
        "location.updated",
        {
            "driver_id": driver_id,
            "latitude": latitude,
            "longitude": longitude,
            "ride_id": ride_id
        }
    )


async def start_location_consumer():
    pubsub = r.pubsub()
    await pubsub.subscribe(
        "driver.status_changed",
        "ride.started",
        "ride.completed"
    )

    async for message in pubsub.listen():
        if message["type"] == "message":
            event_name = message["channel"]
            data = json.loads(message["data"])

            if event_name == "driver.status_changed":
                if data["status"] == "online":
                    add_online_driver(data["driver_id"])

                elif data["status"] == "offline":
                    remove_online_driver(data["driver_id"])
                    delete_driver_location(data["driver_id"])

            elif event_name == "ride.started":
                print(f"🚗 Tracking started for ride {data['ride_id']}")
            
            elif event_name == "ride.completed":
                delete_driver_location(data["driver_id"])
                remove_online_driver(data["driver_id"])
                print(f"🏁 Tracking stopped for ride {data['ride_id']}")
