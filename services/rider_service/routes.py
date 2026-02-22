from fastapi import APIRouter, HTTPException

from services.rider_service.models import RiderCreate, RiderResponse
from services.rider_service.events import event_rider_registered

from database.session import sessionDep
from database.models import Riders

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
