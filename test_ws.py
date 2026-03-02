import asyncio
import websockets
import json


async def test_rider():
    uri = "ws://localhost:8000/ws/rider/1"

    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"Rider received: {json.dumps(data, indent=2)}")


async def test_driver():
    """Connect as driver and listen"""
    uri = "ws://localhost:8000/ws/driver/1"

    async with websockets.connect(uri) as ws:
        print("Driver connected!")

        async for message in ws:
            data = json.loads(message)
            print(f"Driver received: {json.dumps(data, indent=2)}")


async def run_both():
    """Run rider and driver listeners together"""
    await asyncio.gather(
        test_rider(),
        test_driver()
    )


if __name__ == "__main__":
    asyncio.run(run_both())