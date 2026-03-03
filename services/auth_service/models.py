from pydantic import BaseModel

class RiderRegister(BaseModel):
    phone: str
    password: str
    payment_method: str = "cash"


class DriverRegister(BaseModel):
    phone: str
    password: str
    insurance_policy_number: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str