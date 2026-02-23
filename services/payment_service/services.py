from fastapi import HTTPException
from sqlmodel import select
from typing import Optional

from database.models import (
    Rides,
    RidesStatus,
    Payment,
    Fares,
    Riders,
)

from services.payment_service.models import PaymentStatus

def calculate_total_fare(fare: Fares) -> float:
    per_km_rate = 50.0
    total = (
        fare.base_price +
        (fare.distance * per_km_rate)
    ) * fare.surge_multiplier

    return round(total, 2)

async def get_payment_by_ride(
        ride_id: int,
        session
):
    result = session.execute(
        select(Payment).where(
            Payment.ride_id == ride_id
        )
    )

    return result.scalars().one_or_none()

async def create_payment(
        ride_id: int,
        rider_id: int,
        session
):
    ride = session.get(Rides, ride_id)
    if not ride:
        raise HTTPException(
            status_code=400,
            detail="ride not found"
        )
    
    if ride.status != RidesStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"ride not completed = {ride.status}"
        )
    
    existing = await get_payment_by_ride(ride_id, session)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Payment already exists for this ride"
        )
    
    fare: Optional[Fares] = session.get(Fares, ride.fares_id)
    if not fare:
        raise HTTPException(
            status_code=400,
            detail="fare not found"
        )
    
    rider: Optional[Riders] = session.get(Riders, rider_id)
    if not rider:
        raise HTTPException (
            status_code=400,
            detail="fare not found"
        )
    
    total_amount = calculate_total_fare(fare)

    payment = Payment(
        ride_id=ride_id,
        rider_id=rider_id,
        amount=total_amount,
        payment_method=rider.payment_method,
        status=PaymentStatus.COMPLETED
    )

    session.add(payment)
    session.commit()
    session.refresh(payment)

    return {
        "success": True,
        "payment_id": payment.id,
        "ride_id": ride_id,
        "rider_id": rider_id,
        "amount": total_amount,
        "payment_method": rider.payment_method,
        "status": payment.status
    }
    
async def process_refund(
    payment_id: int,
    reason: str,
    session
) -> dict:
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )
    
    if payment.status != PaymentStatus.COMPLETED:
        raise HTTPException(
            status_code=404,
            detail="Payment status is not completed"
        )
    
    payment.status = PaymentStatus.REFUNDED

    session.add(payment)
    session.commit()
    session.refresh(payment)

    return {
        "success": True,
        "payment_id": payment.id,
        "amount": payment.amount,
        "status": payment.status,
        "reason": reason
    }

async def get_all_payment_rider(rider_id: int, session):
    result = session.exec(
        select(Payment).where(
            Payment.rider_id == rider_id,
            Payment.status == PaymentStatus.COMPLETED
        )
    )

    return result.scalars().all()