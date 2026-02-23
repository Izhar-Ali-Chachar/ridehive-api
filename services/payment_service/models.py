from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    WALLET = "wallet"

class PaymentCreate(SQLModel):
    """Manually create a payment"""
    ride_id: int
    rider_id: int


class RefundRequest(SQLModel):
    """Request a refund"""
    payment_id: int
    reason: str

class PaymentResponse(SQLModel):
    """Payment details"""
    id: int
    ride_id: int
    rider_id: int
    amount: float
    payment_method: PaymentMethod
    status: PaymentStatus
    created_at: datetime


class RefundResponse(SQLModel):
    """Refund result"""
    payment_id: int
    status: PaymentStatus
    amount: float
    message: str


class PaymentSummary(SQLModel):
    """Summary for a rider"""
    rider_id: int
    total_rides: int
    total_spent: float
    payments: list[PaymentResponse]