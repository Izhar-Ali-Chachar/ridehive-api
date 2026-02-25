from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from database.models import (
    DriverStatus
)


class DriverCreate(BaseModel):
    insurance_policy_number: int

class DriverStatusUpdate(BaseModel):
    status: DriverStatus

class DriverRespone(BaseModel):
    id: int
    insurance_policy_number: int
    status: DriverStatus
    created_at: datetime
    
class RideAcceptResponse(BaseModel):
    ride_id: int
    driver_id: int
    status: str
    message: str
    rider_id: int


class RideStartResponse(BaseModel):
    ride_id: int
    status: str
    start_time: datetime
    message: str


class RideCompleteResponse(BaseModel):
    ride_id: int
    status: str
    start_time: datetime
    end_time: datetime
    total_fare: float
    message: str

class VehicleCreate(BaseModel):
    """Driver adds a vehicle"""
    driver_id: int
    make: str
    model: str
    year: int
    license_plate: str