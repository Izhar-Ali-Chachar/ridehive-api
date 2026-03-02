import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets.rider_ws import rider_manager, listen_for_rider_events
from websockets.driver_ws import driver_manager, listen_for_driver_events

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/rider/{rider_id}")
async def rider_websocket(
    websocket: WebSocket,
    rider_id: int
):
    await rider_manager.connect(rider_id, websocket)

    listener_task = asyncio.create_task(
        listen_for_rider_events(rider_id)
    )

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Rider {rider_id} sent: {data}")

    except WebSocketDisconnect:
        rider_manager.disconnect(rider_id)
        listener_task.cancel()
        print(f"Rider {rider_id} disconnected")

@router.websocket("/ws/driver/{driver_id}")
async def driver_websocket(
    websocket: WebSocket,
    driver_id: int
):
    await driver_manager.connect(driver_id, websocket)

    listener_task = asyncio.create_task(
        listen_for_driver_events(driver_id)
    )

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Driver {driver_id} sent: {data}")

    except WebSocketDisconnect:
        driver_manager.disconnect(driver_id)
        listener_task.cancel()
        print(f"Driver {driver_id} disconnected")