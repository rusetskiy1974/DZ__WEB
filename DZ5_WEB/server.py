import asyncio
from datetime import datetime
import logging
import websockets
import names
from aiofile import async_open
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from main import main, parse_command

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, ws, message: str):
        if self.clients:
            [await client.send(f"{ws.name}: {message}") for client in self.clients if client != ws]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distribute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.lower().split()[0] == 'exchange':
                async with async_open("log.txt", 'a') as afp:
                    await afp.write(f'Called command exchange {datetime.now()}\n')
                await ws.send(f"<<< Wait")
                try:
                    day = int(parse_command(message.lower().split()))
                    if day in range(10):
                        answer = await asyncio.create_task(main(day))
                        await self.display(ws, answer)
                    else:
                        raise ValueError

                except (ValueError, TypeError, IndexError):
                    await ws.send(f"<<< Incorrect value, days may be in range 1 - 10")

            else:
                for client in self.clients:
                    if client != ws:
                        await client.send(f"{ws.name}: {message}")

    async def display(self, ws, data):
        pattern = "|{:^15}|{:^15}|{:^15}|"
        for el in data:
            for key, value in el.items():
                await ws.send(f'Date : {key}')
                await ws.send(f'{pattern.format("currency", "sale", "purchase")}')
                for key1, value1 in value.items():
                    currency = key1
                    buy = value1['purchase']
                    sale = value1['sale']
                    await ws.send((pattern.format(currency, sale, buy)))


async def main_server():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main_server())
