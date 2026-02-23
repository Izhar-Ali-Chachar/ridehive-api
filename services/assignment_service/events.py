import redis
import json
from datetime import datetime
from database.session import get_session
from services.assignment_service.services import process_assignment

r = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)


def publish_event(event_name: str, data: dict):
    data["timestamp"] = str(datetime.now())

    r.publish(event_name, json.dumps(data))
    print(f"✅ Event fired: {event_name}")


async def handle_ride_requested(data: dict):
    """
    Listens to ride.requested event
    Calls shared service logic
    Fires result event
    """
    ride_id = data["ride_id"]
    rider_id = data["rider_id"]
    pickup_lat = data["pickup_lat"]
    pickup_lng = data["pickup_lng"]

    print(f"🚗 Assigning driver for ride {ride_id}...")

    # use shared session
    session = get_session()

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
            publish_event("ride.assigned", {
                "ride_id": ride_id,
                "rider_id": rider_id,
                "driver_id": result["driver_id"],
                "vehicle_id": result["vehicle_id"],
                "distance_km": result["distance_km"]
            })
        else:
            # fire failure event
            publish_event("assignment.failed", {
                "ride_id": ride_id,
                "rider_id": rider_id,
                "reason": result["reason"]
            })

    finally:
        session.close()


async def start_assignment_consumer():
    """
    Listen to ride.requested events
    """
    pubsub = r.pubsub()
    pubsub.subscribe("ride.requested")

    print("🎯 Assignment consumer started...")

    for message in pubsub.listen():
        if message["type"] == "message":
            event = message["channel"]
            data = json.loads(message["data"])

            if event == "ride.requested":
                await handle_ride_requested(data)