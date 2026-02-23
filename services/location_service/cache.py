import redis
import json
from datetime import datetime


r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
    ssl=False
)

def save_driver_location(
        driver_id: int,
        latitude: float,
        longitude: float
):
    key = f"driver:location:{driver_id}"
    data = {
        "driver_id": driver_id,
        "longitude": longitude,
        "latitude": latitude,
        "updated_at": str(datetime.now())
    }

    r.setex(
        key,
        30,
        json.dumps(data)
    )
    print(f"Location saved: Driver {driver_id} → {latitude}, {longitude}")


def get_driver_location(
        driver_id: int
):
    key = f"driver:location:{driver_id}"

    data = r.get(key)

    if not data:
        return None
    
    return json.loads(data) #type: ignore

def delete_driver_location(
        driver_id: int
):
    key = f"driver:location:{driver_id}"
    r.delete(key)
    print(f"Location removed: Driver {driver_id} went offline")

def add_online_driver(
        driver_id: int
):
    r.sadd(
        "drivers:online",
        driver_id
    )
    print(f"Driver {driver_id} added to online pool")

def remove_online_driver(
        driver_id: int
):
    r.srem(
        "drivers:online",
        driver_id
    )

def get_all_online_drivers() -> list[int]:
    drivers = r.smembers("drivers:online")
    if not drivers:
        return []
    return [int(d) for d in drivers] #type: ignore

def get_nearby_drivers(
    latitude: float,
    longitude: float,
    radius_km: float
):
    import math

    online_drivers = get_all_online_drivers()
    nearby = []

    for driver in online_drivers:
        location = get_driver_location(driver)

        if not location:
            return None
        
        distance = calculate_distance(
            latitude,
            longitude,
            location["latitude"],
            location["longitude"]
        )

        if distance <= radius_km:
            nearby.append(
                {
                    "driver_id": driver,
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "distance_km": round(distance, 2)
                }
            )

        nearby.sort(key=lambda x: x["distance_km"])
        return nearby
    
def calculate_distance(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float
) -> float:
    import math

    R = 6371

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) *
        math.cos(lat2_rad) *
        math.sin(delta_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance