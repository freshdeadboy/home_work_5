import asyncio
import aiohttp
import datetime

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def get_exchange_rates(days, currencies):
    results = []
    base_url = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
    today = datetime.date.today()

    for i in range(days):
        current_date = today - datetime.timedelta(days=i)
        formatted_date = current_date.strftime("%d.%m.%Y")
        url = base_url + formatted_date
        data = await fetch(url)
        exchange_rates = {
            formatted_date: {}
        }
        for currency in data["exchangeRate"]:
            if currency["currency"] in currencies:
                exchange_rates[formatted_date][currency["currency"]] = {
                    "sale": currency["saleRateNB"],
                    "purchase": currency["purchaseRateNB"]
                }
        results.append(exchange_rates)
    return results

async def main():
    days = int(input("Введіть кількість днів: "))
    if days > 10:
        print("Недопустима кількість днів. Максимально дозволено 10.")
        return
    currencies = input("Введіть коди валют (через пробіл): ").split()
    exchange_rates = await get_exchange_rates(days, currencies)
    print(exchange_rates)

if __name__ == "__main__":
    asyncio.run(main())