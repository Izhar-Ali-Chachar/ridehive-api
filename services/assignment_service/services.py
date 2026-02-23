from services.location_service.cache import (
    get_all_online_drivers,
    calculate_distance
)

from services.assignment_service.lock import (
    is_locked,
    acquire_lock,
    release_lock
)

from database.session import sessionDep
from database.models import (
    Rides,
    RidesStatus,
    Vehicle,
    Drivers,
    DriverStatus
)

from sqlmodel import select


def find_nearest_driver(
    pickup_lat: float,
    pickup_lng: float
) -> dict | None:
    all_drivers = get_all_online_drivers()

    if not all_drivers or not isinstance(all_drivers, list):
        return None

    nearest = None
    min_distance = float('inf')

    for driver in all_drivers:

        if is_locked(driver["driver_id"]): #type: ignore
            continue

        distance = calculate_distance(
            lat1=pickup_lat,
            lng1=pickup_lng,
            lat2=driver["latitude"], #type: ignore
            lng2=driver["longitude"] #type: ignore
        )

        # only within 10km
        if distance <= 10.0 and distance < min_distance:
            min_distance = distance
            nearest = {
                "driver_id": int(driver["driver_id"]), #type: ignore
                "distance_km": distance
            }

    return nearest

async def get_driver_vehicle(
    driver_id: int,
    session: sessionDep
) -> Vehicle | None:
    
    result = await session.execute(
        select(Vehicle).where(
            Vehicle.driver_id == driver_id,
            Vehicle.status == "active"
        )
    )

    return result.scalars().one_or_none()

async def assign_driver_to_ride(
    ride_id: int,
    driver_id: int,
    vehicle_id: int,
    session: sessionDep
) -> bool:
    try:
        ride = await session.get(Rides, ride_id)
        driver = await session.get(Drivers, driver_id)

        if not ride or not driver:
            return False

        # assign driver
        ride.status = RidesStatus.ACCEPTED
        ride.driver_id = driver_id
        ride.vehicle_id = vehicle_id

        # set driver on trip
        driver.status = DriverStatus.ON_TRIP

        session.add(ride)
        session.add(driver)
        await session.commit()

        return True

    except Exception as e:
        print(f"❌ Assignment error: {e}")
        await session.rollback()
        return False
    
async def process_assignment(
    ride_id: int,
    rider_id: int,
    pickup_lat: float,
    pickup_lng: float,
    session: sessionDep
) -> dict:
    # step 1 — find nearest driver
    nearest = find_nearest_driver(pickup_lat, pickup_lng)

    if not nearest:
        return {
            "success": False,
            "reason": "No drivers available nearby"
        }

    driver_id = nearest["driver_id"]

    # step 2 — lock driver
    locked = acquire_lock(driver_id)
    if not locked:
        # driver just taken, try again
        return await process_assignment(
            ride_id, rider_id,
            pickup_lat, pickup_lng,
            session
        )

    try:
        # step 3 — get vehicle
        vehicle = await get_driver_vehicle(driver_id, session)
        if not vehicle:
            return {
                "success": False,
                "reason": "Driver has no active vehicle"
            }

        # step 4 — assign in database
        success = assign_driver_to_ride(
            ride_id=ride_id,
            driver_id=driver_id,
            vehicle_id=vehicle.id, #type: ignore
            session=session
        )

        if not success:
            return {
                "success": False,
                "reason": "Database assignment failed"
            }

        return {
            "success": True,
            "driver_id": driver_id,
            "vehicle_id": vehicle.id,
            "distance_km": nearest["distance_km"]
        }

    finally:
        # always release lock
        release_lock(driver_id)