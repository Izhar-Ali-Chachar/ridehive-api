from pydantic import BaseModel
from typing import Optional


class AssignmentRequest(BaseModel):
    ride_id: int
    pickup_lat: float
    pickup_lng: float

class AssignmentResponse(BaseModel):
    ride_id: int
    driver_id: int
    distance_km: float
    message: str

class AssignmentFailed(BaseModel):
    ride_id: int
    message: str
    reason: str