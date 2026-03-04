from fastapi import APIRouter, Depends, HTTPException

from sqlmodel import select, or_

from services.rider_service.models import (
    RiderResponse,
    RiderUpdate,
    RideRequestResponse,
    RideRequest,
    UpdatePaymentMethod
)
from services.rider_service.events import (
    event_rider_registered,
    event_ride_requested,
    event_ride_cancelled
)

from database.session import sessionDep
from database.models import (
    Riders,
    Rides,
    RidesStatus,
    Fares,
    RiderPaymentMethod
)
from core.auth import require_rider
from typing import Annotated

router = APIRouter(prefix="/rider", tags=["Rider"])

@router.get("/{rider_id}", response_model=RiderResponse)
async def get_rider(rider_id: int, session: sessionDep):
    rider = await session.get(Riders, rider_id)

    if not rider:
        raise HTTPException(
            status_code=400,
            detail="rider not found"
        )
    
    return rider

@router.get("/profile")
async def get_profile(
    session: sessionDep,
    current_user: dict = Depends(require_rider)
):
    rider_id = int(current_user["sub"])
    rider = await session.get(Riders, rider_id)

    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")

    return {
        "id": rider.id,
        "phone": rider.phone,
        "payment_method": rider.payment_method,
        "created_at": rider.created_at
    }

@router.patch("/payment-method")
async def update_payment_method(
    data: UpdatePaymentMethod,
    session: sessionDep,
    current_user: dict = Depends(require_rider)
):
    rider_id = int(current_user["sub"])
    rider = await session.get(Riders, rider_id)

    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")

    rider.payment_method = RiderPaymentMethod(data.payment_method)
    session.add(rider)
    await session.commit()
    await session.refresh(rider)

    return {
        "message": "Payment method updated",
        "payment_method": rider.payment_method
    }

@router.patch("/{rider_id}", response_model=RiderResponse)
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

@router.post("/rides/request", response_model=RideRequestResponse)
async def ride_request(
    ride_data: RideRequest,
    session: sessionDep,
    current_user: Annotated[dict, Depends(require_rider)]
):
    rider_id = int(current_user["sub"])
    rider = await session.get(Riders, rider_id)

    if not rider:
        raise HTTPException(
            status_code=400,
            detail="rider not found"
        )
    
    result = await session.execute(
        select(Rides).where(
            Rides.rider_id == rider_id,
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
        rider_id = rider_id,
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

@router.get("/rides/{ride_id}/status")
async def get_ride_status(
    ride_id: int,
    session: sessionDep,
    _: Annotated[dict, Depends(require_rider)]
):
    ride = await session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=400,
            detail="ride not found"
        )
    
    return {
        "ride_id": ride.id,
        "status": ride.status,
        "driver_id": ride.driver_id,
        "start_time": ride.start_time,
        "end_time": ride.end_time
    }

@router.patch("/rides/{ride_id}/cancel")
async def ride_cancel(
    session: sessionDep,
    ride_id: int,
    rider_id: int,
    _: Annotated[dict, Depends(require_rider)],
    reason: str = "No reason provided"
):
    ride = await session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=400,
            detail="ride not found"
        )
    
    if ride.rider_id != rider_id:
        raise HTTPException(
            status_code=403,
            detail="This is not your ride"
        )
    
    # can only cancel if not already started
    if ride.status == RidesStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a ride that is already in progress"
        )

    if ride.status == RidesStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a completed ride"
        )
    
    if ride.status == RidesStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail="Ride is already cancelled"
        )
    
    ride.status = RidesStatus.CANCELLED
    session.add(ride)
    await session.commit()


    # fire event
    event_ride_cancelled(
        ride_id=ride_id,
        rider_id=rider_id,
        reason=reason
    )

    return {
        "message": "Ride cancelled successfully",
        "ride_id": ride_id,
        "status": ride.status
    }

@router.get("/{rider_id}/rides")
async def get_rider_rides(
    rider_id: int,
    session: sessionDep,
    _: Annotated[dict, Depends(require_rider)]
):
    rider = await session.get(Riders, rider_id)
    if not rider:
        raise HTTPException(
            status_code=400,
            detail="rider not found"
        )
    
    result = await session.execute(
        select(Rides).where(
            Rides.rider_id == rider_id
        )
    )

    rides = result.scalars().all()

    return {
        "rider_id": rider_id,
        "total_rides": len(rides),
        "rides": rides
    }
