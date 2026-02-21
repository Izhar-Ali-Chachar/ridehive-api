from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.db.session import sessionDep

from app.db.models import (
    Rides, Riders, Drivers, Fares, Payment,
    RidesStatus, DriverStatus, PaymentStatus
)

from sqlmodel import select

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

    session.add(rides)
    await session.commit()
    await session.refresh(rides)

    return rides
    
@router.post("{ride_id}/accepted")
async def accepted_ride(ride_id: int, driver_id: int, session: sessionDep):
    ride = await session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=400,
            detail="Ride not found"
        )
    
    if ride.status != RidesStatus.REQUESTED:
        raise HTTPException(
            status_code=400,
            detail="Ride cannot be accepted. Current status: {ride.status}"
        )
    
    driver = await session.get(Drivers, driver_id)
    if not driver:
        raise HTTPException(
            status_code=400,
            detail="Driver not found"
        )
    
    if driver.status != DriverStatus.ONLINE:
        raise HTTPException(
            status_code=400,
            detail="Driver is not available"
        )
    
    ride.status = RidesStatus.ACCEPTED

    driver.status = DriverStatus.ON_TRIP

    session.add(ride)
    session.add(driver)
    await session.commit()
    await session.refresh(ride)

    return {
        "message": "Ride accepted successfully",
        "ride_id": ride.id,
        "status": ride.status,
        "driver_status": driver.status
    }


@router.post("{ride_id}/started")
async def ride_started(
    ride_id: int,
    session: sessionDep
):
    ride = await session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=400,
            detail="Ride not found"
        )
    
    if ride.status != RidesStatus.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail="Ride cannot be accepted. Current status: {ride.status}"
        )
    
    ride.status = RidesStatus.IN_PROGRESS
    ride.start_time = datetime.now()

    session.add(ride)
    await session.commit()
    await session.refresh(ride)

    return {
        "message": "Ride started",
        "ride_id": ride.id,
        "status": ride.status,
        "start_time": ride.start_time
    }

@router.post("{ride_id}/completed")
async def ride_completed(ride_id: int, session: sessionDep):
    ride = await session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=400,
            detail="Ride not found"
        )
    
    if ride.status != RidesStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail="Ride cannot be in_progress. Current status: {ride.status}"
        )
    
    driver = await session.get(Drivers, ride.driver_id)
    if not driver:
        raise HTTPException(
            status_code=400,
            detail="Driver not found"
        )

    ride.status = RidesStatus.COMPLETED
    ride.end_time = datetime.now()

    driver.status = DriverStatus.ONLINE

    session.add(ride)
    session.add(driver)
    await session.commit()
    await session.refresh(ride)

    return {
        "message": "Ride completed",
        "ride_id": ride.id,
        "status": ride.status,
        "start_time": ride.start_time,
        "end_time": ride.end_time
    }

@router.post("{ride_id}/payment")
async def ride_payment(ride_id: int, session: sessionDep):
    ride = await session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=400,
            detail="Ride not found"
        )
    
    if ride.status != RidesStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Ride cannot be completed. Current status: {ride.status}"
        )
    
    result = await session.execute(
        select(Payment).where(Payment.ride_id == ride_id)
    )
    existing_payment = result.scalar_one_or_none()

    if existing_payment:
        raise HTTPException(
            status_code=400,
            detail="Payment already exists for this ride"
        )
    
    fare = await session.get(Fares, ride.fares_id)
    if not fare:
        raise HTTPException(status_code=404, detail="Fare not found")
    
    rider = await session.get(Riders, ride.rider_id)
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")

    total_amount = fare.base_price * fare.surge_multiplier

    payment = Payment(
        rider_id = ride.rider_id,
        ride_id = ride_id,
        amount = total_amount,
        payment_method = rider.payment_method,
        staus = PaymentStatus.COMPLETED
    )

    session.add(payment)
    await session.commit()
    await session.refresh(payment)

    return {
        "message": "Payment successful",
        "payment_id": payment.id,
        "ride_id": ride_id,
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "status": payment.status
    }
