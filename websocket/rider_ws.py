import asyncio
import redis.asyncio as aioredis
import json
from fastapi import WebSocket, WebSocketDisconnect

class RiderConnectionManager:
    def __init__(self):
        self.active: dict[int, WebSocket] = {}

    async def connect(self, rider_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active[rider_id] = websocket
        print(f"Rider {rider_id} connected")

    def disconnect(self, rider_id: int):
        if rider_id in self.active:
            del self.active[rider_id]
            print(f"Rider {rider_id} disconnected")

    async def send(self, rider_id: int, data: dict):
        websocket = self.active.get(rider_id)
        if websocket:
            try:
                await websocket.send_json(data)
            except Exception as e:
                print(f"Failed to send to rider {rider_id}: {e}")
                self.disconnect(rider_id)

    async def broadcast(self, data: dict):
        for rider_id, websocket in list(self.active.items()):
            try:
                await websocket.send_json(data)
            except Exception:
                self.disconnect(rider_id)

rider_manager = RiderConnectionManager()

async def listen_for_rider_events(rider_id: int):

    r = aioredis.Redis(
        host= "localhost",
        port= 6379,
        decode_responses= True
    )

    pubsub = r.pubsub()

    await pubsub.subscribe(
        "ride.assigned",
        "ride.accepted",
        "ride.started",
        "ride.completed",
        "location.updated",
        "payment.completed",
        "payment.failed",
        "assignment.failed"
    )

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        event = message["channel"]
        data = json.loads(message["data"])

        if data.get("rider_id") != rider_id:
            continue

        payload = format_rider_message(event, data)

        if payload:
            await rider_manager.send(rider_id, payload)
            print(f"Sent to rider {rider_id}: {event}")

def format_rider_message(event: str, data: dict) -> dict | None:
    if event == "ride.assigned":
        return {
            "type": "ride_assigned",
            "message": "Driver found and heading to you!",
            "driver_id": data.get("driver_id"),
            "distance_km": data.get("distance_km"),
            "ride_id": data.get("ride_id")
        }

    elif event == "ride.started":
        return {
            "type": "ride_started",
            "message": "Your trip has begun!",
            "ride_id": data.get("ride_id"),
            "start_time": data.get("start_time")
        }

    elif event == "ride.completed":
        return {
            "type": "ride_completed",
            "message": "You have arrived!",
            "ride_id": data.get("ride_id"),
            "total_fare": data.get("total_fare")
        }

    elif event == "location.updated":
        return {
            "type": "driver_location",
            "driver_id": data.get("driver_id"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude")
        }

    elif event == "payment.completed":
        return {
            "type": "payment_done",
            "message": f"Payment of PKR {data.get('amount')} successful!",
            "amount": data.get("amount"),
            "payment_method": data.get("payment_method")
        }

    elif event == "payment.failed":
        return {
            "type": "payment_failed",
            "message": "Payment failed. Please try again.",
            "reason": data.get("reason")
        }

    elif event == "assignment.failed":
        return {
            "type": "no_drivers",
            "message": "No drivers available nearby. Please try again."
        }

    return None

