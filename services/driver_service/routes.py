from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from database.session import sessionDep
from database.models import (
    Drivers, 
    DriverStatus,
    Rides,
    RidesStatus,
    Vehicle,
    VehicleStatus,
    Fares
)

from services.driver_service.models import (
    DriverCreate, 
    DriverRespone, 
    DriverStatusUpdate, 
    RideAcceptResponse,
    RideStartResponse,
    RideCompleteResponse
)

from services.driver_service.events import (
    event_driver_registered, 
    event_driver_status_changed,
    event_ride_accepted,
    event_ride_started,
    event_ride_completed
)

router = APIRouter(
    prefix="/driver",
    tags=["Driver"]
)


@router.post("/register", response_model = DriverRespone)
async def driver_register(driver_data: DriverCreate, session: sessionDep):
    result = await session.execute(
        select(Drivers).where(Drivers.insurance_policy_number == driver_data.insurance_policy_number)
    )

    existing_driver = result.scalar_one_or_none()

    if existing_driver:
        raise HTTPException(
            status_code=400,
            detail="driver already exist"
        )

    driver = Drivers(
        **driver_data.model_dump()
    )

    session.add(driver)
    await session.commit()
    await session.refresh(driver)

    if driver.id is not None:
        event_driver_registered(driver_id=driver.id)

    return driver

@router.patch("{driver_id}/status", response_model=DriverRespone)
async def driver_status(driver_id: int, data: DriverStatusUpdate, session: sessionDep):
    driver = await session.get(Drivers, driver_id)

    if not driver:
        raise HTTPException(
            status_code=400,
            detail="driver not found"
        )
    
    if driver.status == DriverStatus.ON_TRIP:
        raise HTTPException(
            status_code=400,
            detail="driver on trip can not change status"
        )
    
    if data.status == DriverStatus.ON_TRIP:
        raise HTTPException(
            status_code=400,
            detail="Cannot manually set status to on_trip"
        )
    
    old_status = driver.status
    driver.status = data.status

    session.add(driver)
    await session.commit()
    await session.refresh(driver)

    if old_status != driver.status:
        if driver.id is not None:
            event_driver_status_changed(
                driver.id,
                driver.status
            )

    return driver


@router.patch("rides/{ride_id}/accept", response_model=RideAcceptResponse)
async def ride_accept(
    ride_id: int,
    driver_id: int,
    session: sessionDep
):
    ride = await session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=400,
            detail="ride not found"
        )
    
    if ride.status != RidesStatus.REQUESTED:
        raise HTTPException(
            status_code=400,
            detail="ride is not requested"
        )
    
    driver = await session.get(Drivers, driver_id)
    if not driver:
        raise HTTPException(
            status_code=400,
            detail="driver not found"
        )
    
    if driver.status != DriverStatus.ONLINE:
        raise HTTPException(
            status_code=400,
            detail="driver not ONLINE"
        )
    
    result = await session.execute(
        select(Vehicle).where(
            Vehicle.driver_id == driver_id
        )
    )

    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(
            status_code=400,
            detail="vehicle not found"
        )

    if vehicle.status != VehicleStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="vehicle is not active"
        )
    
    if vehicle.id is None:
        raise HTTPException(
            status_code=400,
            detail="vehicle id is invalid"
        )
    
    ride.status = RidesStatus.ACCEPTED
    ride.driver_id = driver_id
    ride.vehicle_id = vehicle.id

    driver.status = DriverStatus.ON_TRIP

    session.add(ride)
    session.add(driver)
    await session.commit()
    await session.refresh(ride)
    
    event_ride_accepted(
        ride_id=ride_id,
        driver_id=driver_id,
        rider_id=ride.rider_id
    )

    return RideAcceptResponse(
        ride_id=ride_id,
        driver_id=driver_id,
        status=ride.status,
        message="Ride accepted. Head to pickup location.",
        rider_id=ride.rider_id
    )

@router.patch("rides/{ride_id}/start", response_model=RideAcceptResponse)
async def ride_start(
    ride_id: int,
    driver_id: int,
    session: sessionDep
):
    ride = await session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=400,
            detail="ride not found"
        )
    
    if ride.status != RidesStatus.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail="ride is not accepted"
        )
    
    if ride.driver_id != driver_id:
        raise HTTPException(
            status_code=400,
            detail="You are not assigned to this ride"
        )
    
    ride.status = RidesStatus.IN_PROGRESS
    ride.start_time = datetime.now()

    session.add(ride)
    await session.commit()
    await session.refresh(ride)
    
    event_ride_started(
        ride_id=ride_id,
        driver_id=driver_id,
        rider_id=ride.rider_id,
        start_time=str(ride.start_time)
    )


    return RideStartResponse(
        ride_id=ride_id,
        status=ride.status,
        start_time=ride.start_time,
        message="Ride started. Have a safe trip!"
    )

@router.patch("rides/{ride_id}/complete", response_model=RideCompleteResponse)
async def ride_complete(
    ride_id: int,
    driver_id: int,
    actual_distance: float,
    actual_duration: int,
    session: sessionDep
):
    ride = await session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=400,
            detail="ride not found"
        )
    
    if ride.status != RidesStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail="ride is not in progress"
        )
    
    if ride.driver_id != driver_id:
        raise HTTPException(
            status_code=400,
            detail="You are not assigned to this ride"
        )
    
    if not ride.start_time:
        raise HTTPException(
            status_code=400,
            detail="ride start time is not set"
        )
    
    fare = await session.get(Fares, ride.fares_id)
    if not fare:
        raise HTTPException(
            status_code=404,
            detail="Fare not found"
        )
    
    fare.distance = actual_distance
    fare.duration = actual_duration

    per_km_rate = 50.0
    total_fare = (fare.base_price + (actual_distance * per_km_rate)) * fare.surge_multiplier

    driver = await session.get(Drivers, driver_id)

    if not driver:
        raise HTTPException(
            status_code=400,
            detail="driver not found"
        )
    
    ride.status = RidesStatus.COMPLETED
    ride.end_time = datetime.now()

    driver.status = DriverStatus.ONLINE

    session.add(fare)
    session.add(ride)
    session.add(driver)
    await session.commit()
    await session.refresh(ride)

    event_ride_completed(
        ride_id=ride_id,
        driver_id=driver_id,
        rider_id=ride.rider_id,
        total_fare=round(total_fare, 2),
        end_time=str(ride.end_time)
    )

    return RideCompleteResponse(
        ride_id=ride_id,
        status=ride.status,
        start_time=ride.start_time,
        end_time=ride.end_time,
        total_fare=round(total_fare, 2),
        message="Ride completed. Payment is being processed."
    )