import time
import asyncio
import websockets


async def hello(websocket):
    name = await websocket.recv()
    print(f"<<< {name}")

    await websocket.send(f"Checking database")

    await asyncio.sleep(3)

    await websocket.send(f"Some data for you, but one more check")

    await asyncio.sleep(1)

    await websocket.send(f"finish")


async def start_server():
    async with websockets.serve(hello, "localhost", 8765) as server:
        await server.server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\nShutdown")