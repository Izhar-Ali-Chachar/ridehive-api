from fastapi import APIRouter, HTTPException

from services.location_service.models import (
    LocationUpdate,
    LocationResponse,
    NearbyDriversRequest,
    NearbyDriversResponse,
    NearbyDriver
)

from services.location_service.cache import (
    save_driver_location,
    get_driver_location,
    get_nearby_drivers,
)

from services.location_service.events import (
    event_location_updated
)

router = APIRouter(prefix="/location", tags=["Location"])


@router.post("/update")
async def location_update(data: LocationUpdate):
    await save_driver_location(
        data.driver_id,
        data.latitude,
        data.longitude
    )

    event_location_updated(
        data.driver_id,
        data.latitude,
        data.longitude,
        ride_id=data.ride_id
    )

    return LocationResponse(
        driver_id=data.driver_id,
        latitude=data.latitude,
        longitude=data.longitude,
        updated_at=str(__import__('datetime').datetime.now())
    )

@router.get("/{driver_id}", response_model=LocationResponse)
async def get_location(
    driver_id: int
):
    location = await get_driver_location(driver_id)

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Driver location not found. Driver may be offline."
        )
    
    return LocationResponse(
        driver_id=location["driver_id"],
        latitude=location["latitude"],
        longitude=location["longitude"],
        updated_at=location["updated_at"]
    )

@router.post("/nearby", response_model=NearbyDriversResponse)
async def get_nearby_drivers_endpoint(data: NearbyDriversRequest):
    nearby = await get_nearby_drivers(
        latitude=data.latitude,
        longitude=data.longitude,
        radius_km=data.radius_km
    )

    if not nearby:
        raise HTTPException(
            status_code=404,
            detail="No drivers available nearby. Try again in a moment."
        )

    return NearbyDriversResponse(
        total=len(nearby),
        drivers=[NearbyDriver(**d) for d in nearby]
    )