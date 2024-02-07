import asyncio
import logging
import websockets
import concurrent.futures

logging.basicConfig(level=logging.INFO)


async def send(executor, ws):
    loop = asyncio.get_event_loop()

    while True:
        result = await loop.run_in_executor(executor, input)
        await ws.send(result)


async def listen(ws):
    async for message in ws:
        logging.info(message)


async def start_client(hostname, port):
    ws_resource_url = f"ws://{hostname}:{port}"

    async with websockets.connect(ws_resource_url) as ws:
        listen_coroutine = listen(ws)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = send(executor, ws)

            await asyncio.gather(listen_coroutine, future)


if __name__ == '__main__':
    asyncio.run(start_client('localhost', 8080))
