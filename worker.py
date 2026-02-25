import asyncio
import redis.asyncio as aioredis
import json
from database.session import async_session
from services.notification_service.events import start_notification_consumer
from services.assignment_service.events import start_assignment_consumer
from services.payment_service.events import start_payment_consumer
from services.location_service.events import start_location_consumer


async def main():
    print("🚀 Starting all workers...")

    await asyncio.gather(
        start_notification_consumer(),
        start_assignment_consumer(),
        start_payment_consumer(),
        start_location_consumer(),
    )


if __name__ == "__main__":
    # ✅ own fresh event loop
    # no conflicts with FastAPI
    asyncio.run(main())