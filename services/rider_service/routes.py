from fastapi import APIRouter, HTTPException

from sqlmodel import select, or_

from services.rider_service.models import (
    RiderCreate,
    RiderResponse,
    RiderUpdate,
    RideRequestResponse,
    RideRequest
)
from services.rider_service.events import (
    event_rider_registered,
    event_ride_requested
)

from database.session import sessionDep
from database.models import (
    Riders,
    Rides,
    RidesStatus,
    Fares
)

app = APIRouter(prefix="/rider")

@app.post("/register")
async def register_rider(rider: RiderCreate, session: sessionDep):
    db_rider = Riders(
        **rider.model_dump()
    )

    session.add(db_rider)
    await session.commit()
    await session.refresh(db_rider)

    if not db_rider.id:
        raise HTTPException(
            status_code=400,
            detail="rider id not found"
        )

    event_rider_registered(
        db_rider.id,
        db_rider.payment_method
    )

    return db_rider

@app.get("{rider_id}", response_model=RiderResponse)
async def get_rider(rider_id: int, session: sessionDep):
    rider = await session.get(Riders, rider_id)

    if not rider:
        raise HTTPException(
            status_code=400,
            detail="rider not found"
        )
    
    return rider

@app.patch("{rider_id}", response_model=RiderResponse)
async def update_rider(rider_id: int, rider_update: RiderUpdate, session: sessionDep):
    rider = await session.get(Riders, rider_id)

    if not rider:
        raise HTTPException(
            status_code=400,
            detail="rider not found"
        )
    
    if rider_update.payment_method is not None:
        rider.payment_method = rider_update.payment_method #type: ignore

    session.add(rider)
    await session.commit()
    await session.refresh(rider)

    return rider

@app.post("/ride/requested", response_model=RideRequestResponse)
async def ride_request(
    ride_data: RideRequest,
    session: sessionDep
):
    rider = await session.get(Riders, ride_data.rider_id)

    if not rider:
        raise HTTPException(
            status_code=400,
            detail="rider not found"
        )
    
    result = await session.execute(
        select(Rides).where(
            Rides.rider_id == ride_data.rider_id,
            or_(
                Rides.status == RidesStatus.ACCEPTED,
                Rides.status == RidesStatus.IN_PROGRESS
            )
        )
    )

    active_ride = result.scalar_one_or_none()

    if active_ride:
        raise HTTPException(
            status_code=400,
            detail="You already have an active ride"
        )
    
    import math
    distance_km = math.sqrt(
        (ride_data.pickup_lat - ride_data.dropoff_lat) ** 2 +
        (ride_data.pickup_lng - ride_data.dropoff_lng) ** 2
    ) * 111

    base_price = 200
    per_km_rate = 50.0

    estimated_fare = base_price + (distance_km * per_km_rate)

    fare = Fares(
        base_price=base_price,
        distance=distance_km,
        duration=0,
        currency="PKR",
        surge_multiplier=1.0
    )

    session.add(fare)
    await session.commit()
    await session.refresh(fare)

    ride = Rides(
        rider_id = ride_data.rider_id,
        fares_id = fare.id,
        status = RidesStatus.REQUESTED
    )

    session.add(ride)
    await session.commit()
    await session.refresh(ride)

    if not ride.id or not rider.id:
        raise HTTPException(
            status_code=400,
            detail="ride or rider id not found"
        )

    event_ride_requested(
        ride.id,
        rider.id,
        ride_data.pickup_lat,
        ride_data.pickup_lng,
        ride_data.dropoff_lat,
        ride_data.dropoff_lng,
        round(estimated_fare, 2)
    )

    return RideRequestResponse(
        ride_id=ride.id,
        status=ride.status,
        message="Looking for a driver...",
        estimated_fare=round(estimated_fare, 2),
        pickup_lat=ride_data.pickup_lat,
        pickup_lng=ride_data.pickup_lng,
        dropoff_lat=ride_data.dropoff_lat,
        dropoff_lng=ride_data.dropoff_lng
    )

    
    
