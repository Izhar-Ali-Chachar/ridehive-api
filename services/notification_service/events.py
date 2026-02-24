import redis
import json
from datetime import datetime
from database.session import get_session
from services.notification_service.service import send_notification
from services.notification_service.models import (
    NotificationType,
    NotificationChannel,
    RecipientType
)

r = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)


async def handle_rider_registered(data: dict, session):
    await send_notification(
        session=session,
        recipient_id=data["rider_id"],
        recipient_type=RecipientType.RIDER,
        title="Welcome to Ridehive!",
        message="Your account is ready. Book your first ride now.",
        type=NotificationType.SUCCESS,
        channel=NotificationChannel.PUSH
    )

async def handle_driver_registered(data: dict, session):
    await send_notification(
        session=session,
        recipient_id=data["driver_id"],
        recipient_type=RecipientType.DRIVER,
        title="Welcome Driver!",
        message="Your account is ready. Go online to start accepting rides.",
        type=NotificationType.SUCCESS,
        channel=NotificationChannel.PUSH
    )

async def handle_ride_requested(data: dict, session):
    await send_notification(
        session=session,
        recipient_id=data["rider_id"],
        recipient_type=RecipientType.RIDER,
        title="Finding your driver...",
        message="We are searching for the nearest driver for you.",
        type=NotificationType.INFO,
        channel=NotificationChannel.PUSH,
        ride_id=data["ride_id"]
    )


async def handle_ride_assigned(data: dict, session):
    distance = data.get("distance_km", 0)
    await send_notification(
        session=session,
        recipient_id=data["rider_id"],
        recipient_type=RecipientType.RIDER,
        title="Driver Found!",
        message=f"Your driver is {distance} km away and heading to you.",
        type=NotificationType.SUCCESS,
        channel=NotificationChannel.PUSH,
        ride_id=data["ride_id"]
    )


async def handle_ride_started(data: dict, session):
    await send_notification(
        session=session,
        recipient_id=data["rider_id"],
        recipient_type=RecipientType.RIDER,
        title="Ride Started!",
        message="Your trip has begun. Enjoy your ride.",
        type=NotificationType.INFO,
        channel=NotificationChannel.PUSH,
        ride_id=data["ride_id"]
    )


async def handle_ride_completed(data: dict, session):
    """Tell both rider and driver trip is done"""

    # notify rider
    await send_notification(
        session=session,
        recipient_id=data["rider_id"],
        recipient_type=RecipientType.RIDER,
        title="Ride Completed ",
        message=f"You have arrived. Total fare: PKR {data.get('total_fare', 0)}",
        type=NotificationType.SUCCESS,
        channel=NotificationChannel.PUSH,
        ride_id=data["ride_id"]
    )

    # notify driver
    await send_notification(
        session=session,
        recipient_id=data["driver_id"],
        recipient_type=RecipientType.DRIVER,
        title="Ride Completed",
        message="Great job! You are now available for new rides.",
        type=NotificationType.SUCCESS,
        channel=NotificationChannel.PUSH,
        ride_id=data["ride_id"]
    )


async def handle_payment_completed(data: dict, session):
    """Send receipt to rider"""
    await send_notification(
        session=session,
        recipient_id=data["rider_id"],
        recipient_type=RecipientType.RIDER,
        title="Payment Successful",
        message=(
            f"PKR {data.get('amount', 0)} paid via "
            f"{data.get('payment_method', 'card')}. "
            f"Thank you for riding with Uber!"
        ),
        type=NotificationType.SUCCESS,
        channel=NotificationChannel.PUSH,
        ride_id=data["ride_id"]
    )


async def handle_payment_failed(data: dict, session):
    """Alert rider payment failed"""
    await send_notification(
        session=session,
        recipient_id=data["rider_id"],
        recipient_type=RecipientType.RIDER,
        title="Payment Failed",
        message="Your payment could not be processed. Please try again.",
        type=NotificationType.ERROR,
        channel=NotificationChannel.PUSH,
        ride_id=data.get("ride_id")
    )


async def handle_assignment_failed(data: dict, session):
    """Tell rider no drivers available"""
    await send_notification(
        session=session,
        recipient_id=data["rider_id"],
        recipient_type=RecipientType.RIDER,
        title="No Drivers Available",
        message="Sorry, no drivers are available nearby. Please try again.",
        type=NotificationType.WARNING,
        channel=NotificationChannel.PUSH,
        ride_id=data["ride_id"]
    )


async def handle_ride_cancelled(data: dict, session):
    """Tell driver ride was cancelled"""
    await send_notification(
        session=session,
        recipient_id=data["driver_id"],
        recipient_type=RecipientType.DRIVER,
        title="Ride Cancelled",
        message=f"The rider cancelled the ride. Reason: {data.get('reason', 'No reason')}",
        type=NotificationType.WARNING,
        channel=NotificationChannel.PUSH,
        ride_id=data["ride_id"]
    )

def start_notification_consumer():
    pubsub = r.pubsub()

    # subscribe to every event
    pubsub.subscribe(
        "rider.registered",
        "driver.registered",
        "ride.requested",
        "ride.assigned",
        "ride.started",
        "ride.completed",
        "payment.completed",
        "payment.failed",
        "assignment.failed",
        "ride.cancelled"
    )

    print("🔔 Notification consumer started...")

    for message in pubsub.listen():
        if message["type"] == "message":
            event = message["channel"]
            data = json.loads(message["data"])

            session = get_session()

            try:
                # route to correct handler
                handlers = {
                    "rider.registered":   handle_rider_registered,
                    "driver.registered":  handle_driver_registered,
                    "ride.requested":     handle_ride_requested,
                    "ride.assigned":      handle_ride_assigned,
                    "ride.started":       handle_ride_started,
                    "ride.completed":     handle_ride_completed,
                    "payment.completed":  handle_payment_completed,
                    "payment.failed":     handle_payment_failed,
                    "assignment.failed":  handle_assignment_failed,
                    "ride.cancelled":     handle_ride_cancelled
                }

                handler = handlers.get(event)
                if handler:
                    handler(data, session)
                else:
                    print(f"No handler for event: {event}")

            except Exception as e:
                print(f"Notification error: {e}")

            finally:
                session.close()