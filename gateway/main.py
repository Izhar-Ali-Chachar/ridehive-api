from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database.session import create_tables
from services.rider_service.routes import router as rider_router
from services.driver_service.routes import router as driver_router
from services.location_service.routes import router as location_router
from services.assignment_service.routes import router as assignment_router
from services.payment_service.routes import router as payment_router
from services.notification_service.routes import router as notification_router
from websocket.router import router as ws_router


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    print("Starting RideHive API...")
    await create_tables()
    print("Database ready")
    yield
    print("Shutting down...")


app = FastAPI(
    title="RideHive API",
    lifespan=lifespan_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rider_router)
app.include_router(driver_router)
app.include_router(location_router)
app.include_router(assignment_router)
app.include_router(payment_router)
app.include_router(notification_router)
app.include_router(ws_router)


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "RideHive API running"}