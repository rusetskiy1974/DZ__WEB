import aiohttp
import asyncio
import platform
import sys
import json
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from websockets_chat_server import start_server
from websockerts_chat_client import start_client
from websocker_server import start_server


DATE_FORMAT = '%d.%m.%Y'
CURRENCY_RATE_SEARCH = ('USD', 'EUR')
EXCHANGE_RESULT = []


class HttpError(Exception):
    pass


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f'Connection error: {url}', str(err))


async def main(days):
    responses = []
    for day in range(days):
        date = (datetime.now() - timedelta(days=day)).date().strftime(DATE_FORMAT)
        responses.append(request('https://api.privatbank.ua/p24api/exchange_rates?json&date=' + str(date)))

    try:
        loop = asyncio.get_running_loop()
        full_data_exchange = await asyncio.gather(*responses)
        with ThreadPoolExecutor() as pool:
            futures = [loop.run_in_executor(pool, take_data_from_response, day) for day in full_data_exchange]
            result_ = await asyncio.gather(*futures)
            return result_
    except HttpError as er:
        print(er)
        return None


def take_data_from_response(day):
    day_result = {}
    for money in day['exchangeRate']:
        if money['currency'] in CURRENCY_RATE_SEARCH:
            day_result.update({money['currency']: {'sale': money['saleRate'], 'purchase': money['purchaseRate']}})
    return {day['date']: day_result}


def save_result(data_result):
    with open('storage/data.json', 'w', encoding='utf-8') as file:
        json.dump(data_result, file, ensure_ascii=False, indent=4)


def get_sys_argv_1(volume):
    try:
        if int(volume[1]) > 10:
            raise ValueError('Max days volume must be <= 10')
        return int(volume[1])
    except ValueError as err:
        print(err)
        exit()
    except IndexError:
        return 1


def get_sys_argv_2(volume):
    try:
        if volume[2]:
            return (*volume[2].upper().split(','),)
    except IndexError:
        return ()


#

if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    days_ = get_sys_argv_1(sys.argv)
    CURRENCY_RATE_SEARCH += get_sys_argv_2(sys.argv)
    result = asyncio.run(main(days_))
    save_result(result)
    with ProcessPoolExecutor(2) as executor:

    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\nShutdown")

    asyncio.run(start_client('localhost', 8765))

