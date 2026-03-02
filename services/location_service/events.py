import redis
import redis.asyncio as aioredis
import json
from datetime import datetime
from services.location_service.cache import (
    add_online_driver,
    remove_online_driver,
    delete_driver_location,
    save_driver_location
)


import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


def publish_event(
    event_name: str,
    data: dict
) -> None:

    data["timestamp"] = datetime.now().isoformat()
    payload = json.dumps(data)
    r.publish(event_name, payload)
    print(f"Event published: {event_name} → {data}")

def event_location_updated(
    driver_id: int,
    latitude: float,
    longitude: float,
    ride_id: int
) -> None:
    publish_event(
        "location.updated",
        {
            "driver_id": driver_id,
            "latitude": latitude,
            "longitude": longitude,
            "ride_id": ride_id
        }
    )

async def start_location_consumer() -> None:

    r = aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )

    pong = await r.ping() # type: ignore
    print(f"Location Redis: {'Connected' if pong else 'Failed'}")

    pubsub = r.pubsub()

    await pubsub.subscribe(
        "driver.status_changed",
        "ride.started",
        "ride.completed"
    )

    print("Location consumer started and listening...")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        event_name = message["channel"]
        data = json.loads(message["data"])

        print(f"Received: {event_name}")

        try:
            if event_name == "driver.status_changed":
                driver_id = int(data["driver_id"])
                status = data.get("status")

                if status == "online":
                    await add_online_driver(driver_id)

                elif status == "offline":
                    await remove_online_driver(driver_id)

            elif event_name == "ride.started":
                ride_id = data.get("ride_id")
                driver_id = int(data.get("driver_id", 0))
                print(f"Tracking started → ride {ride_id} driver {driver_id}")

            elif event_name == "ride.completed":
                driver_id = int(data["driver_id"])
                ride_id = data.get("ride_id")

                await delete_driver_location(driver_id)
                print(f"🏁 Tracking stopped → ride {ride_id} driver {driver_id}")

        except KeyError as e:
            print(f"Missing key in event data: {e}")
        except ValueError as e:
            print(f"Value error: {e}")
        except Exception as e:
            print(f"Location consumer error: {e}")