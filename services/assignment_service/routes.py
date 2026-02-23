from fastapi import APIRouter, HTTPException, Depends
from database.session import sessionDep
from database.models import Rides, RidesStatus
from services.assignment_service.models import (
    AssignmentRequest,
    AssignmentResponse
)
from services.assignment_service.services import process_assignment
from services.location_service.cache import get_all_online_drivers
from services.assignment_service.lock import is_locked

router = APIRouter(
    prefix="/assignment",
    tags=["Driver Assignment"]
)


@router.post("/assign", response_model=AssignmentResponse)
async def manual_assign(
    data: AssignmentRequest,
    session: sessionDep
):
    ride = await session.get(Rides, data.ride_id)
    if not ride:
        raise HTTPException(
            status_code=404,
            detail="Ride not found"
        )

    if ride.status != RidesStatus.REQUESTED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot assign. Status: {ride.status}"
        )

    result = await process_assignment(
        ride_id=data.ride_id,
        rider_id=ride.rider_id,
        pickup_lat=data.pickup_lat,
        pickup_lng=data.pickup_lng,
        session=session
    )

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["reason"]
        )

    return AssignmentResponse(
        ride_id=data.ride_id,
        driver_id=result["driver_id"],
        distance_km=result["distance_km"],
        message="Driver assigned successfully"
    )

@router.get("/{ride_id}")
async def get_assignment_status(
    ride_id: int,
    session: sessionDep
):
    ride = await session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=404,
            detail="Ride not found"
        )

    if not ride.driver_id:
        return {
            "ride_id": ride_id,
            "status": ride.status,
            "assigned": False,
            "message": "Still searching for driver..."
        }

    return {
        "ride_id": ride_id,
        "status": ride.status,
        "assigned": True,
        "driver_id": ride.driver_id,
        "vehicle_id": ride.vehicle_id,
        "message": "Driver assigned"
    }

@router.get("/available/count")
async def get_available_count():
    all_drivers = get_all_online_drivers()
    available = [
        d for d in all_drivers
        if not is_locked(d["driver_id"])
    ]
    return {
        "total_online": len(all_drivers),
        "total_available": len(available),
        "total_locked": len(all_drivers) - len(available)
    }