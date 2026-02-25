import redis.asyncio as aioredis
import json
import math
from datetime import datetime
from redis.asyncio import Redis


def get_redis() -> Redis:
    return aioredis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
        ssl=False
    )


LOCATION_EXPIRY = 600  # 10 minutes

async def save_driver_location(
    driver_id: int,
    latitude: float,
    longitude: float
) -> None:
    r = get_redis()
    try:
        key = f"driver:location:{driver_id}"
        data = {
            "driver_id": driver_id,
            "latitude": latitude,
            "longitude": longitude,
            "updated_at": datetime.now().isoformat()
        }
        await r.setex(key, LOCATION_EXPIRY, json.dumps(data))
        await r.sadd("drivers:online", driver_id)  # type: ignore[misc]
        print(f"Saved: driver {driver_id} → {latitude}, {longitude}")
    finally:
        await r.aclose()

async def get_driver_location(
    driver_id: int
) -> dict | None:
    r = get_redis()
    try:
        key = f"driver:location:{driver_id}"
        data = await r.get(key)
        if not data:
            return None
        return json.loads(str(data))
    finally:
        await r.aclose()

async def delete_driver_location(
    driver_id: int
) -> None:
    r = get_redis()
    try:
        await r.delete(f"driver:location:{driver_id}")
        await r.srem("drivers:online", driver_id)  # type: ignore[misc]
        print(f"🗑️ Removed: driver {driver_id}")
    finally:
        await r.aclose()

async def add_online_driver(
    driver_id: int
) -> None:
    r = get_redis()
    try:
        await r.sadd("drivers:online", driver_id)  # type: ignore[misc]
        print(f"✅ Driver {driver_id} added to online pool")
    finally:
        await r.aclose()

async def remove_online_driver(
    driver_id: int
) -> None:
    r = get_redis()
    try:
        await r.srem("drivers:online", driver_id)  # type: ignore[misc]
        await r.delete(f"driver:location:{driver_id}")
        print(f"Driver {driver_id} removed from online pool")
    finally:
        await r.aclose()


async def get_all_online_drivers() -> list[dict]:
    r = get_redis()
    try:
        raw_ids: set[str] = await r.smembers(  "drivers:online") # type: ignore
    finally:
        await r.aclose()

    if not raw_ids:
        print("No online drivers in pool")
        return []

    drivers: list[dict] = []

    for driver_id in raw_ids:
        location = await get_driver_location(int(driver_id))

        if not location:
            # expired — clean up
            r2 = get_redis()
            try:
                await r2.srem(  # type: ignore[misc]
                    "drivers:online",
                    driver_id
                )
            finally:
                await r2.aclose()
            print(f"⚠️ Driver {driver_id} expired, removed")
            continue

        drivers.append(location)

    print(f"Online drivers with location: {len(drivers)}")
    return drivers

async def get_nearby_drivers(
    latitude: float,
    longitude: float,
    radius_km: float = 10.0
) -> list[dict]:
    all_drivers = await get_all_online_drivers()
    nearby = []

    for driver in all_drivers:
        distance = calculate_distance(
            lat1=latitude,
            lng1=longitude,
            lat2=driver["latitude"],
            lng2=driver["longitude"]
        )

        if distance <= radius_km:
            nearby.append({
                "driver_id": driver["driver_id"],
                "latitude": driver["latitude"],
                "longitude": driver["longitude"],
                "distance_km": round(distance, 2)
            })

    nearby.sort(key=lambda x: x["distance_km"])
    return nearby

def calculate_distance(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float
) -> float:
    R = 6371
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2 +
        math.cos(lat1_r) *
        math.cos(lat2_r) *
        math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c