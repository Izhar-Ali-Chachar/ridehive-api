# main.py

import asyncio
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database.session import create_tables


def start_workers_in_thread():
    from services.notification_service.events import start_notification_consumer
    from services.assignment_service.events import start_assignment_consumer
    from services.location_service.events import start_location_consumer
    from services.payment_service.events import start_payment_consumer

    async def run():
        await asyncio.gather(
            start_notification_consumer(),
            start_assignment_consumer(),
            start_location_consumer(),
            start_payment_consumer(),
        )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    print("Starting Uber API...")
    await create_tables()

    worker_thread = threading.Thread(
        target=start_workers_in_thread,
        daemon=True,
        name="WorkerThread"
    )
    worker_thread.start()
    print("Workers started")

    yield

    print("Shutting down...")


app = FastAPI(
    title="Uber Clone API",
    lifespan=lifespan_handler
)

from services.rider_service.routes import router as rider_router
from services.driver_service.routes import router as driver_router
from services.location_service.routes import router as location_router
from services.assignment_service.routes import router as assignment_router
from services.payment_service.routes import router as payment_router
from services.notification_service.routes import router as notification_router

app.include_router(rider_router)
app.include_router(driver_router)
app.include_router(location_router)
app.include_router(assignment_router)
app.include_router(payment_router)
app.include_router(notification_router)


@app.get("/")
async def health_check():
    return {"status": "ok"}