from fastapi import APIRouter, HTTPException
from app.db.session import sessionDep

from app.db.models import (
    Rides, Riders, Drivers, Fares,
    RidesStatus, DriverStatus
)

router = APIRouter(prefix="rides")

@router.post("/request")
async def request_ride(
    rider_id: int,
    driver_id: int,
    vehicle_id: int,
    fares_id: int,
    session: sessionDep
):
    rider = await session.get(Riders, rider_id)
    if not rider:
        raise HTTPException(
            status_code=400,
            detail="Rider not found"
        )
    
    driver = await session.get(Drivers, driver_id)
    if not driver:
        raise HTTPException(
            status_code=400,
            detail="Driver not found"
        )
    
    if driver.status != DriverStatus.ONLINE:
        raise HTTPException(
            status_code=404,
            detail="Driver is not available"
        )
    
    fare = await session.get(Fares, fares_id)
    if not fare:
        raise HTTPException(
            status_code=400,
            detail="fare not found"
        )

    rides = Rides(
        rider_id = rider_id,
        driver_id = driver_id,
        fares_id = fares_id,
        vehicle_id = vehicle_id,
        status = RidesStatus.REQUESTED
    )
    
