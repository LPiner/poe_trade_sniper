import requests
import structlog
import json
from poe_trade_sniper.db import get_currency_price, add_currency_price
logger = structlog.get_logger()

with open('resources/currency_mappings.json', 'r') as f:
    CURRENCY_MAPPINGS = json.loads(f.read())


def get_currency_rates(league: str):
    logger.info('Attempting to get currency rates.', league=league)

    uri = "http://poe.ninja/api/Data/GetCurrencyOverview?league=%s" % league

    rates = requests.get(uri).json()['lines']
    with open('resources/currency_rates.json', 'w+') as f:
        f.write(json.dumps(rates))
    return rates


def convert_currency_abbreviation(abbreviation: str) -> str:
    currency = ''
    for c in CURRENCY_MAPPINGS:
        if abbreviation in CURRENCY_MAPPINGS[c]:
            currency = c
    #logger.info('Converted currency names.', currency=currency, abbreviation=abbreviation)
    return currency


def convert_currency_to_chaos(currency: str, amount: float) -> int:
    conversion = 0
    c = get_currency_price(currency)
    if c:
        conversion = c[2] * amount
    if not c or not conversion:
        logger.warn('Was unable to convert currency.', currency=currency, amount=amount, conversion=conversion, price_entry=c)
    return conversion

