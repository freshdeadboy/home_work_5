import asyncio
import logging
import datetime

import httpx
import names
import websockets
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from aiofile import AIOFile, LineReader
from aiopath import AsyncPath

logging.basicConfig(level=logging.INFO)

async def request(url: str) -> dict | str:
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code == 200:
            result = r.json()
            return result
        else:
            return "Не вийшло в мене взнати курс. Приват не відповідає :)"

async def get_exchange(days: int):
    results = []
    base_url = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
    today = datetime.date.today()

    for i in range(days):
        current_date = today - datetime.timedelta(days=i)
        formatted_date = current_date.strftime("%d.%m.%Y")
        url = base_url + formatted_date
        response = await request(url)
        results.append({formatted_date: response})
    
    return results

async def log_exchange_command():
    async with AIOFile("exchange.log", "a") as afp:
        await afp.write(f"{datetime.datetime.now()} - exchange command executed\n")

class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

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
            if message.startswith("exchange"):
                parts = message.split()
                if len(parts) == 2 and parts[1].isdigit():
                    days = int(parts[1])
                    await log_exchange_command()
                    exchange = await get_exchange(days)
                    await self.send_to_clients(str(exchange))
                else:
                    await self.send_to_clients("Невірний формат команди exchange. Введіть exchange <кількість днів>")
            elif message == 'Hello server':
                await self.send_to_clients("Привіт мої карапузи!")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())