from fastapi import APIRouter, HTTPException
from typing import Optional

from services.payment_service.models import (
    PaymentCreate,
    PaymentResponse,
    RefundRequest,
    RefundResponse,
    PaymentSummary
)

from services.payment_service.services import (
    create_payment,
    get_payment_by_ride,
    process_refund,
    get_all_payment_rider
)

from database.session import sessionDep
from database.models import Payment


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

@router.post("/create", response_model=PaymentResponse)
async def manual_create_payment(
    data: PaymentCreate,
    session: sessionDep
):
    result = await create_payment(
        ride_id = data.ride_id,
        rider_id = data.rider_id,
        session = session
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["reason"]
        )

    payment: Optional[Payment] = session.get(
        Payment, result["payment_id"]
    )

    if not payment:
        raise HTTPException(
            status_code=500,
            detail="Payment created but not found"
        )

    return payment

@router.get("/ride/{ride_id}", response_model=PaymentResponse)
async def get_payment(
    ride_id: int,
    session: sessionDep
):
    payment = await get_payment_by_ride(ride_id, session)

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found for this ride"
        )

    return payment

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_by_id(
    payment_id: int,
    session: sessionDep
):
    payment = await session.get(Payment, payment_id)

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    return payment

@router.post("/refund", response_model=RefundResponse)
def refund_payment(
    data: RefundRequest,
    session: sessionDep
):
    result = process_refund(
        data.payment_id,
        data.reason,
        session
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["reason"]
        )

    return RefundResponse(
        payment_id=result["payment_id"],
        status=result["status"],
        amount=result["amount"],
        message=f"Refund processed. Reason: {result['reason']}"
    )
    
@router.get("/rider/{rider_id}", response_model=PaymentSummary)
def get_rider_payments(
    rider_id: int,
    session: sessionDep
):
    payments = get_all_payment_rider(rider_id, session)

    total_spent = sum(p.amount for p in payments)

    return PaymentSummary(
        rider_id=rider_id,
        total_rides=len(payments),
        total_spent=round(total_spent, 2),
        payments=payments
    )
