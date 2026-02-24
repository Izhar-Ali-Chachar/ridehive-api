# main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from services.rider_service.routes import router as rider_router
from services.driver_service.routes import router as driver_router
from services.location_service.routes import router as location_router
from services.assignment_service.routes import router as assignment_router
from services.payment_service.routes import router as payment_router
from services.notification_service.routes import router as notification_router
from database.session import create_tables


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    print("🚀 Starting Uber API...")
    
    await create_tables()

    print("Database ready")

    yield

    print("🛑 Shutting down...")


app = FastAPI(
    title="Uber Clone API",
    version="1.0.0",
    lifespan=lifespan_handler
)

app.include_router(rider_router)
app.include_router(driver_router)
app.include_router(location_router)
app.include_router(assignment_router)
app.include_router(payment_router)
app.include_router(notification_router)


@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "message": "Uber API is running"
    }