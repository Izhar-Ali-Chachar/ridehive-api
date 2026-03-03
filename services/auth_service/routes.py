from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from database.session import sessionDep
from database.models import Riders, Drivers
from core.auth import (
    hash_password,
    verify_password,
    create_access_token
)

from services.auth_service.models import (
    TokenResponse,
    RiderRegister,
    DriverRegister
)

from core.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/rider/register", response_model=TokenResponse)
async def rider_register(
    data: RiderRegister,
    session: sessionDep
):
    result = await session.execute(
        select(Riders).where(Riders.phone == data.phone)
    )
    rider = result.scalar_one_or_none()

    if rider:
        raise HTTPException(
            status_code=400,
            detail="rider already exists"
        )

    rider = Riders(
        phone=data.phone,
        password_hash=hash_password(data.password),
        payment_method=data.payment_method
    )
    session.add(rider)
    await session.commit()
    await session.refresh(rider)

    if not rider.id:
        raise HTTPException(
            status_code=500,
            detail="Failed to create rider"
        )

    token = create_access_token(
        user_id=rider.id,
        role="rider"
    )

    return TokenResponse(
        access_token=token,
        user_id=rider.id,
        role="rider"
    )

@router.post("/driver/register", response_model=TokenResponse)
async def driver_register(
    data: DriverRegister,
    session: sessionDep
):
    # check phone not taken
    result = await session.execute(
        select(Drivers).where(Drivers.phone == data.phone)
    )
    
    driver = result.scalar_one_or_none()
    if driver:
        raise HTTPException(
            status_code=400,
            detail="Driver with this phone already exists"
        )

    # check insurance not taken
    result2 = await session.execute(
        select(Drivers).where(
            Drivers.insurance_policy_number == data.insurance_policy_number
        )
    )
    insurance = result2.scalar_one_or_none()
    if insurance:
        raise HTTPException(
            status_code=400,
            detail="Insurance number already registered"
        )

    driver = Drivers(
        phone=data.phone,
        password_hash=hash_password(data.password),
        insurance_policy_number=data.insurance_policy_number
    )
    session.add(driver)
    await session.commit()
    await session.refresh(driver)

    if not driver.id:
        raise HTTPException(
            status_code=500,
            detail="Failed to create driver"
        )

    token = create_access_token(
        user_id=driver.id,
        role="driver"
    )

    return TokenResponse(
        access_token=token,
        user_id=driver.id,
        role="driver"
    )

@router.post("/rider/login", response_model=TokenResponse)
async def rider_login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: sessionDep = Depends()
):
    result = await session.execute(
        select(Riders).where(Riders.phone == form.username)
    )
    rider = result.scalar_one_or_none()
    if not rider or not verify_password(form.password, rider.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid phone or password"
        )
    
    if not rider.id:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve rider"
        )

    token = create_access_token(
        user_id=rider.id,
        role="rider"
    )

    return TokenResponse(
        access_token=token,
        user_id=rider.id,
        role="rider"
    )

@router.post("/driver/login", response_model=TokenResponse)
async def driver_login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: sessionDep = Depends()
):
    result = await session.execute(
        select(Drivers).where(Drivers.phone == form.username)
    )
    driver = result.scalar_one_or_none()

    if not driver or not verify_password(form.password, driver.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid phone or password"
        )

    if not driver.id:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve driver"
        )

    token = create_access_token(
        user_id=driver.id,
        role="driver"
    )

    return TokenResponse(
        access_token=token,
        user_id=driver.id,
        role="driver"
    )


@router.get("/me")
async def get_me(
    session: sessionDep,
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user["sub"])
    role = current_user["role"]

    if role == "rider":
        rider = await session.get(Riders, user_id)
        if not rider:
            raise HTTPException(status_code=404, detail="Rider not found")
        return {
            "id": rider.id,
            "phone": rider.phone,
            "role": "rider",
            "payment_method": rider.payment_method
        }

    elif role == "driver":
        driver = await session.get(Drivers, user_id)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        return {
            "id": driver.id,
            "phone": driver.phone,
            "role": "driver",
            "status": driver.status
        }