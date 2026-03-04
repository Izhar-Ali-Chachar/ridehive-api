import redis.asyncio as aioredis
import json
from fastapi import WebSocket, WebSocketDisconnect


class DriverConnectionManager:
    def __init__(self):
        self.active: dict[int, WebSocket] = {}

    async def connect(self, driver_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active[driver_id] = websocket
        print(f"Driver {driver_id} connected")

    def disconnect(self, driver_id: int):
        if driver_id in self.active:
            del self.active[driver_id]
            print(f"Driver {driver_id} disconnected")

    async def send(self, driver_id: int, data: dict):
        websocket = self.active.get(driver_id)
        if websocket:
            try:
                await websocket.send_json(data)
            except Exception as e:
                print(f"Failed to send to driver {driver_id}: {e}")
                self.disconnect(driver_id)

    async def broadcast(self, data: dict):
        for driver_id, websocket in list(self.active.items()):
            try:
                await websocket.send_json(data)
            except Exception:
                self.disconnect(driver_id)

driver_manager = DriverConnectionManager()


async def listen_for_driver_events(driver_id: int):
    r = aioredis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )

    pubsub = r.pubsub()

    await pubsub.subscribe(
        "ride.assigned",
        "ride.cancelled",
        "payment.completed"
    )

    print(f"👂 Listening for events for driver {driver_id}...")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        event = message["channel"]
        data = json.loads(message["data"])

        if int(data.get("driver_id")) != int(driver_id):
            continue

        payload = format_driver_message(event, data)

        if payload:
            await driver_manager.send(driver_id, payload)
            print(f"Sent to driver {driver_id}: {event}")


def format_driver_message(event: str, data: dict) -> dict | None:
    """
    Format Redis event into clean
    WebSocket message for driver app
    """

    if event == "ride.assigned":
        return {
            "type": "new_ride",
            "message": "New ride request!",
            "ride_id": data.get("ride_id"),
            "rider_id": data.get("rider_id"),
            "pickup_lat": data.get("pickup_lat"),
            "pickup_lng": data.get("pickup_lng"),
            "dropoff_lat": data.get("dropoff_lat"),
            "dropoff_lng": data.get("dropoff_lng"),
            "estimated_fare": data.get("estimated_fare")
        }

    elif event == "ride.cancelled":
        return {
            "type": "ride_cancelled",
            "message": "Rider cancelled the ride.",
            "ride_id": data.get("ride_id"),
            "reason": data.get("reason")
        }

    elif event == "payment.completed":
        return {
            "type": "payment_received",
            "message": f"Payment of PKR {data.get('amount')} received!",
            "amount": data.get("amount"),
            "ride_id": data.get("ride_id")
        }

    return None