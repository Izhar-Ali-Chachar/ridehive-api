import redis.asyncio as aioredis
import json
from datetime import datetime
from database.session import async_session
from services.assignment_service.services import process_assignment

import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

r = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

async def publish_event(event_name: str, data: dict):
    data["timestamp"] = datetime.now().isoformat()

    await r.publish(event_name, json.dumps(data))
    print(f"Event fired: {event_name}")


async def handle_ride_requested(data: dict):
    ride_id = data["ride_id"]
    rider_id = data["rider_id"]
    pickup_lat = data["pickup_lat"]
    pickup_lng = data["pickup_lng"]

    print(f"Assigning driver for ride {ride_id}...")

    
    async with async_session() as session:
        try:
            result = await process_assignment(
                ride_id=ride_id,
                rider_id=rider_id,
                pickup_lat=pickup_lat,
                pickup_lng=pickup_lng,
                session=session
            )

            if result["success"]:
                # fire success event
                await publish_event("ride.assigned", {
                    "ride_id": ride_id,
                    "rider_id": rider_id,
                    "driver_id": result["driver_id"],
                    "vehicle_id": result["vehicle_id"],
                    "distance_km": result["distance_km"]
                })
            else:
                # fire failure event
                await publish_event("assignment.failed", {
                    "ride_id": ride_id,
                    "rider_id": rider_id,
                    "reason": result["reason"]
                })

        finally:
            await session.close()


async def start_assignment_consumer():
    pubsub = r.pubsub()
    await pubsub.subscribe("ride.requested")

    print("🎯 Assignment consumer started...")

    async for message in pubsub.listen():
        if message["type"] == "message":
            event = message["channel"]
            data = json.loads(message["data"])

            if event == "ride.requested":
                await handle_ride_requested(data)