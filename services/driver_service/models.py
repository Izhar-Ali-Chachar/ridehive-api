from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database.models import DriverStatus

class DriverCreate(BaseModel):
    """Register a new driver"""
    insurance_policy_number: str


class DriverStatusUpdate(BaseModel):
    """Update driver status"""
    status: DriverStatus
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class VehicleCreate(BaseModel):
    """Driver adds a vehicle"""
    driver_id: int
    make: str
    model: str
    year: int
    license_plate: str

class DriverResponse(BaseModel):
    id: int
    insurance_policy_number: str
    status: DriverStatus
    created_at: datetime

    class Config:
        from_attributes = True

class RideAcceptResponse(BaseModel):
    ride_id: int
    driver_id: int
    status: str
    message: str
    rider_id: int


class RideStartResponse(BaseModel):
    ride_id: int
    driver_id: int
    rider_id: int
    status: str
    start_time: datetime
    message: str


class RideCompleteResponse(BaseModel):
    ride_id: int
    driver_id: int
    rider_id: int
    status: str
    start_time: datetime
    end_time: datetime
    total_fare: float
    message: str