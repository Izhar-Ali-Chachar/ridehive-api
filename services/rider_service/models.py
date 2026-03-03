from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class RiderPaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    WALLET = "wallet"

class RiderCreate(BaseModel):
    payment_method: RiderPaymentMethod = Field(default=RiderPaymentMethod.CASH)

class RiderUpdate(BaseModel):
    payment_method: Optional[RiderPaymentMethod] = Field(default=None)

class RideRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    ride_type: str = "economy"

class RiderResponse(BaseModel):
    id: int
    payment_method: RiderPaymentMethod
    created_at: datetime

class RideRequestResponse(BaseModel):
    ride_id: int
    status: str
    message: str
    estimated_fare: float
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float

class UpdatePaymentMethod(BaseModel):
    payment_method: RiderPaymentMethod


class PaymentMethodResponse(BaseModel):
    message: str
    payment_method: RiderPaymentMethod