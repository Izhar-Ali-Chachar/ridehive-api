from sqlmodel import SQLModel

class LocationUpdate(SQLModel):
    """
    Driver sends this every 3 seconds
    while on a trip
    """
    driver_id: int
    ride_id: int
    latitude: float
    longitude: float


class NearbyDriversRequest(SQLModel):
    """
    Find drivers near rider's location
    """
    latitude: float
    longitude: float
    radius_km: float = 5.0 

class LocationResponse(SQLModel):
    """Current location of a driver"""
    driver_id: int
    latitude: float
    longitude: float
    updated_at: str


class NearbyDriver(SQLModel):
    """One nearby driver"""
    driver_id: int
    latitude: float
    longitude: float
    distance_km: float


class NearbyDriversResponse(SQLModel):
    """List of nearby drivers"""
    total: int
    drivers: list[NearbyDriver]