from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum as SAEnum
from typing import Optional
from datetime import datetime, UTC

class RiderPaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    WALLET = "wallet"


class DriverStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ON_TRIP = "on_trip"


class RidesStatus(str, Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled" 


class VehicleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Riders(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    payment_method: RiderPaymentMethod = Field(default=RiderPaymentMethod.CASH)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    rides: list["Rides"] = Relationship(back_populates="rider")
    payment: list["Payment"] = Relationship(back_populates="rider")


class Drivers(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    insurance_policy_number: str = Field(unique=True)
    status: DriverStatus = Field(default=DriverStatus.OFFLINE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    rides: list["Rides"] = Relationship(back_populates="driver")
    vehicle: list["Vehicle"] = Relationship(back_populates="driver")


class Vehicle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model: str
    license_plate: str = Field(unique=True)
    make: str
    year: int
    status: VehicleStatus = Field(default=VehicleStatus.ACTIVE)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    driver_id: Optional[int] = Field(default=None, foreign_key="drivers.id")

    driver: Drivers = Relationship(back_populates="vehicle")
    rides: list["Rides"] = Relationship(back_populates="vehicle")


class Fares(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    base_price: float = Field(default=200.0)
    distance: float
    duration: int
    currency: str = Field(default="PKR")
    surge_multiplier: float = Field(default=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    rides: list["Rides"] = Relationship(back_populates="fares")


class Rides(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    status: RidesStatus = Field(default=RidesStatus.REQUESTED)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    rider_id: Optional[int] = Field(default=None, foreign_key="riders.id")
    driver_id: Optional[int] = Field(default=None, foreign_key="drivers.id")
    fares_id: Optional[int] = Field(default=None, foreign_key="fares.id")
    vehicle_id: Optional[int] = Field(default=None, foreign_key="vehicle.id")

    rider: Riders = Relationship(back_populates="rides")
    driver: Drivers = Relationship(back_populates="rides")
    fares: Fares = Relationship(back_populates="rides")
    vehicle: Vehicle = Relationship(back_populates="rides")
    payment: list["Payment"] = Relationship(back_populates="ride")


class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    payment_method: RiderPaymentMethod
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    rider_id: Optional[int] = Field(default=None, foreign_key="riders.id")
    ride_id: Optional[int] = Field(default=None, foreign_key="rides.id")

    rider: Riders = Relationship(back_populates="payment")
    ride: Rides = Relationship(back_populates="payment")