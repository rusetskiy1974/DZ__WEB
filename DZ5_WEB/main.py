import aiohttp
import asyncio
import platform
import logging
import sys
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

DATE_FORMAT = '%d.%m.%Y'
CURRENCY_RATE_SEARCH = ()
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


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


def take_data_from_response(day):
    day_result = {}
    for money in day['exchangeRate']:
        if money['currency'] in CURRENCY_RATE_SEARCH:
            day_result.update({money['currency']: {'sale': money['saleRateNB'], 'purchase': money['purchaseRateNB']}})
    return {day['date']: day_result}


def save_result(data_result):
    with open('storage/data.json', 'w', encoding='utf-8') as file:
        json.dump(data_result, file, ensure_ascii=False, indent=4)


def parse_command(args: list):
    global CURRENCY_RATE_SEARCH
    CURRENCY_RATE_SEARCH = ('USD', 'EUR')
    days = 1
    if len(args) > 1:
        for index in range(len(args)):
            if index == 1:
                days = (args[index])
            if index > 1:
                CURRENCY_RATE_SEARCH += (args[index].strip(',').upper(),)

    return days


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
        save_result(result_)
        return result_
    except HttpError as er:
        return logging.error(f"{er}")


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        days_ = int(parse_command(sys.argv))
        if days_ in range(10):
            logging.info(f"{asyncio.run(main(days_))}")
    except (ValueError,TypeError, IndexError):
        logging.info(f'Incorrect value, days may be in range 1 - 10')


