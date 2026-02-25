import redis
import json

from datetime import datetime


r = redis.Redis(
    host = "localhost",
    port = 6379,
    decode_responses = True
)

def publish_event(
        event_name: str,
        data: dict
):
    data["timestamp"] = datetime.now().isoformat()

    payload = json.dumps(data)

    r.publish(
        event_name,
        payload
    )
    print(f"Event fired: {event_name} → {data}")

def event_driver_registered(driver_id: int):
    publish_event(
        "driver.registered",
        {
            "driver_id": driver_id
        }
    )

def event_driver_status_changed(driver_id: int, status: str):
    publish_event(
        "driver.status_changed",
        {
            "driver_id": driver_id,
            "status": status
        }
    )

def event_ride_accepted(
    ride_id: int,
    driver_id: int,
    rider_id: int
):
    publish_event(
        "ride.accepted",
        {
            "ride_id": ride_id,
            "driver_id": driver_id,
            "rider_id": rider_id
        }
    )

def event_ride_started(
    ride_id: int,
    driver_id: int,
    rider_id: int,
    start_time: str
):
    publish_event(
        "ride.started",
        {
            "ride_id": ride_id,
            "driver_id": driver_id,
            "rider_id": rider_id,
            "start_time": start_time
        }
    )

def event_ride_completed(
    ride_id: int,
    driver_id: int,
    rider_id: int,
    total_fare: float,
    end_time: str
):
    publish_event(
        "ride.completed",
        {
            "ride_id": ride_id,
            "driver_id": driver_id,
            "rider_id": rider_id,
            "total_fare": total_fare,
            "end_time": end_time
        }
    )