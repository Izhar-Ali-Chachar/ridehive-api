import asyncio
import threading


async def run_all_consumers():
    """Run all consumers concurrently"""
    from services.notification_service.events import start_notification_consumer
    from services.assignment_service.events import start_assignment_consumer
    from services.location_service.events import start_location_consumer
    from services.payment_service.events import start_payment_consumer

    print("🚀 Starting all workers...")

    # ✅ run all consumers concurrently
    await asyncio.gather(
        start_notification_consumer(),
        start_assignment_consumer(),
        start_location_consumer(),
        start_payment_consumer(),
    )


if __name__ == "__main__":
    asyncio.run(run_all_consumers())