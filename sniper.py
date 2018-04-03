import re
from poe_trade_sniper.db import init_sqlite3, add_item_to_db, delete_items_by_stash_id, delete_items_older_than_x_minutes, find_items_by_name, alert_item
from poe_trade_sniper.currency import *
from poe_trade_sniper.finders import get_possible_items

logger = structlog.get_logger()

# Lowest margin in decimal percent that we should alert on.
#MIN_MARGIN = .15
MIN_MARGIN = .1

WATCHED_ITEMS = get_possible_items()

# We will ignore items not in this league.

POE_STASH_URI = "http://api.pathofexile.com/public-stash-tabs"

def get_stash_data(change_id: str) -> (str, list):
    #logger.debug("Attempting to pull POE stash data.", change_id=change_id)
    request_stash_data = requests.get(POE_STASH_URI, params={'id': change_id})
    #logger.debug("Finished pulling POE stash data.", runtime=time.time()-start_time, uri=request_stash_data.url)
    try:
        data = request_stash_data.json()
        change_id = data.get('next_change_id', '') 
        if not change_id:
            print(data)
            print(request_stash_data.headers)
        stashes = data.get('stashes', [])
        #logger.debug("Got change ID and Stashes.", change_id=change_id, stash_count=len(stashes))
        return change_id, stashes
    except Exception as e:
        logger.warn("Failed to convert stash data to json.", stash_data=request_stash_data)
        return None, []


def get_price_data(note: str) -> (str, float):
    currency = ''
    units = 0

    note_search = re.search(r'\S+ (\S+) (\S+)', note)
    try:
        currency = note_search.group(2)
        currency = convert_currency_abbreviation(currency)
        raw_price = note_search.group(1)
        if '/' in raw_price:
            numerator, denominator = raw_price.split('/')
            units = float(numerator) / float(denominator)
        else:
            units = float(raw_price)
    except:
        pass
    return currency, units


def find_underpriced_items(item_name: str) -> list:

    under_priced_items = []

    search_items = find_items_by_name(item_name)
    if not search_items or len(search_items) < 5:
        return under_priced_items

    items = []
    for item in search_items:
        if item.price_in_chaos > 0:
            items.append(item)

    # get sort by price.
    items = sorted(items, key=lambda item: item.price_in_chaos)
    # get the lowest 5
    items = items[:5]
    total = 0
    for item in items:
        total += item.price_in_chaos

    average_price = total/len(items)

    price_floor = average_price - (average_price * MIN_MARGIN)

    for item in items:
        item.average_price = average_price
        if item.price_in_chaos <= price_floor and not item.alerted:
            #logger.warn('Found underpriced item!', item=item)
            #logger.warn(
            #    '@%s Hi, I would like to buy [%s] for %s %s in %s. (tab "%s")' % (item[6], item[3], item[4], item[5], item[8], item[2]),
            #    predicted_margin=average_price-item.price,
            #    average_price=average_price,
            #    total_indexed=len(items)
            #)
            under_priced_items.append(item)
            alert_item(item.id)
    return under_priced_items


def get_current_change_id() -> str:
    # once this breaks use http://poe.ninja/stats
    page = requests.get('http://api.poe.ninja/api/Data/GetStats')
    return page.json()['next_change_id']


def parse_items(stash: dict, league: str):
    # No invalid accounts

    for item in stash['items']:

        # Skips items in the wrong league
        if item['league'] != league:
            continue

        # Skips items without a price set
        if not item.get('note', None):
            continue

        currency, units = get_price_data(item['note'])
        if not currency or not units:
            continue

        prefix = re.sub(r'.*<<.*>>', '', item['name']).strip()
        suffix = re.sub(r'.*<<.*>>', '', item['typeLine']).strip()
        real_name = (prefix + ' ' + suffix).strip()

        if real_name in WATCHED_ITEMS:
            add_item_to_db(
                stash['id'],
                stash['stash'],
                real_name,
                units,
                currency,
                stash.get('lastCharacterName'),
                item['league']
            )




