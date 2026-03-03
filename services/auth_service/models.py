from pydantic import BaseModel

from database.models import RiderPaymentMethod

class RiderRegister(BaseModel):
    phone: str
    password: str
    payment_method: RiderPaymentMethod = RiderPaymentMethod.CASH


class DriverRegister(BaseModel):
    phone: str
    password: str
    insurance_policy_number: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str