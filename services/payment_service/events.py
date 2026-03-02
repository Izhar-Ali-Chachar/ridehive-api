import redis
import redis.asyncio as aioredis
import json
from datetime import datetime
from database.session import async_session
from services.payment_service.services import create_payment
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

_sync_r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


def publish_event(event_name: str, data: dict) -> None:
    """✅ sync publish — no await needed"""
    data["timestamp"] = datetime.now().isoformat()
    _sync_r.publish(event_name, json.dumps(data))
    print(f"✅ Event fired: {event_name}")


async def handle_ride_completed(data: dict) -> None:
    ride_id = int(data["ride_id"])
    rider_id = int(data["rider_id"])
    driver_id = int(data["driver_id"])

    print(f"💳 Processing payment for ride {ride_id}...")

    async with async_session() as session:
        try:
            result = await create_payment(
                ride_id=ride_id,
                rider_id=rider_id,
                session=session
            )

            if result["success"]:
                await session.commit()
                print(f"✅ Payment created: PKR {result['amount']}")

                publish_event("payment.completed", {
                    "payment_id": result["payment_id"],
                    "ride_id": ride_id,
                    "rider_id": rider_id,
                    "driver_id": driver_id,
                    "amount": result["amount"],
                    "payment_method": result["payment_method"]
                })

            else:
                print(f"❌ Payment failed: {result['reason']}")

                publish_event("payment.failed", {
                    "ride_id": ride_id,
                    "rider_id": rider_id,
                    "reason": result["reason"]
                })

        except Exception as e:
            await session.rollback()
            print(f"❌ Payment error: {e}")


async def start_payment_consumer() -> None:
    r = aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )

    pong = await r.ping()
    print(f"💳 Payment Redis: {'✅ Connected' if pong else '❌ Failed'}")

    pubsub = r.pubsub()
    await pubsub.subscribe("ride.completed")

    print("💳 Payment consumer started...")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        event = message["channel"]
        data = json.loads(message["data"])

        print(f"💳 Received: {event}")

        if event == "ride.completed":
            await handle_ride_completed(data)
