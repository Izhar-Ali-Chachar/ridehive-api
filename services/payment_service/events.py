# services/payment_service/events.py

import redis
import json
from datetime import datetime
from database.session import get_session
from services.payment_service.services import create_payment

r = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)


def publish_event(event_name: str, data: dict):
    """Fire event to Redis"""
    data["timestamp"] = str(datetime.now())
    r.publish(event_name, json.dumps(data))
    print(f"✅ Event fired: {event_name}")


def handle_ride_completed(data: dict):
    """
    Listens to ride.completed event
    Automatically creates payment
    """
    ride_id = data["ride_id"]
    rider_id = data["rider_id"]
    driver_id = data["driver_id"]

    print(f"💳 Processing payment for ride {ride_id}...")

    session = get_session()

    try:
        # ✅ call shared service logic
        result = create_payment(
            ride_id=ride_id,
            rider_id=rider_id,
            session=session
        )

        if result["success"]:
            print(f"✅ Payment created: {result['amount']} PKR")

            # fire payment completed event
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

            # fire payment failed event
            publish_event("payment.failed", {
                "ride_id": ride_id,
                "rider_id": rider_id,
                "reason": result["reason"]
            })

    except Exception as e:
        print(f"❌ Payment error: {e}")

    finally:
        session.close()


def start_payment_consumer():
    """
    Listen to ride.completed events
    """
    pubsub = r.pubsub()
    pubsub.subscribe("ride.completed")

    print("💳 Payment consumer started...")

    for message in pubsub.listen():
        if message["type"] == "message":
            event = message["channel"]
            data = json.loads(message["data"])

            if event == "ride.completed":
                handle_ride_completed(data)