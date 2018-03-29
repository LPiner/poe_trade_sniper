import requests
import structlog
import time
import json
import re
from poe_trade_sniper.models import POEItem
from poe_trade_sniper.db import init_sqlite3, add_item_to_db, delete_items_by_stash_id, delete_items_older_than_x_minutes, find_items_by_name, alert_item

logger = structlog.get_logger()



# Lowest margin in decimal percent that we should alert on.
#MIN_MARGIN = .15
MIN_MARGIN = .20

# We will ignore items not in this league.
LEAGUE = 'Bestiary'

# Items we want to watch.
WATCHED_ITEMS = [
        "Monstrous Treasure",
        "The Jeweller's Touch",
        "Pools of Wealth",
        "Vaal Winds",
        "The Unbreathing Queen V",
        "Flesh of the Beast",
        "The Feral Lord III",
        "A Dishonourable Death",
        "The Feral Lord V",
        "Lost in the Pages",
        "The Unbreathing Queen IV",
        "Darktongue's Shriek",
        "The Plaguemaw V",
        "Twice Enchanted",
        #"Fire and Brimstone", Price Fixed
        "The Spark and the Flame",
        "Mawr Blaidd",
        "Hunter's Reward",
        "Abandoned Wealth",
        "The Wolven King's Bite",
        "The Iron Bard",
        "The King's Heart",
        "The World Eater",
        "Wealth and Power",
        "Pride Before the Fall",
        "The Dragon's Heart",
        "The Last One Standing",
        "The Wind",
        "The Wolf",
        "The Queen",
        "The Saint's Treasure",
        "The Artist",
        "The Enlightened",
        ]

POE_STASH_URI = "http://api.pathofexile.com/public-stash-tabs"

def get_stash_data(change_id: str) -> (str, list):
    #logger.debug("Attempting to pull POE stash data.", change_id=change_id)
    start_time = time.time()
    request_stash_data = requests.get(POE_STASH_URI, params={'id': change_id})
    #logger.debug("Finished pulling POE stash data.", runtime=time.time()-start_time, uri=request_stash_data.url)
    try:
        data = request_stash_data.json()
        change_id = data.get('next_change_id', '') 
        if not change_id:
            print(data)
        stashes = data.get('stashes', [])
        #logger.debug("Got change ID and Stashes.", change_id=change_id, stash_count=len(stashes))
        return change_id, stashes
    except Exception as e:
        logger.warn("Failed to convert stash data to json.", stash_data=request_stash_data)
        return None, []


def get_price_in_chaos(note: str) -> float:
    if 'chaos' not in note:
        return 0
    raw_price = re.search(r'\S+ (\S+)', note)
    try:
        raw_price = raw_price.group(1)
    except Exception as e:
        return 0

    try:
        if '/' in raw_price:
            numerator, denominator = raw_price.split('/')
            return float(numerator) / float(denominator)
        else:
            return float(raw_price)
    except:
        return 0


def find_underpriced_items(item_name: str) -> list:

    under_priced_items = []

    items = find_items_by_name(item_name)
    if not items or len(items) < 5:
        return under_priced_items

    # get sort by price.
    items = sorted(items, key=lambda item: item.price)
    # get the lowest 5
    items = items[:5]
    total = 0
    for item in items:
        total += item.price

    average_price = total/len(items)

    price_floor = average_price - (average_price * MIN_MARGIN)

    for item in items:
        item.average_price = average_price
        if item.price <= price_floor and not item.alerted:
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

# If we dont do this then we have to crawl the ENTIRE FUCKING STASH HISTORY OF POE WHAT THE FUCK.
change_id = get_current_change_id()


if __name__ == '__main__':
    init_sqlite3()


def parse_items(stash: dict):
    # No invalid accounts

    for item in stash['items']:

        # Skips items in the wrong league
        if item['league'] != LEAGUE:
            continue

        # Skips items without a price set
        if not item.get('note', None):
            continue

        price = get_price_in_chaos(item['note'])
        if not price:
            continue

        prefix = re.sub(r'.*<<.*>>', '', item['name']).strip()
        suffix = re.sub(r'.*<<.*>>', '', item['typeLine']).strip()
        real_name = (prefix + ' ' + suffix).strip()

        if real_name in WATCHED_ITEMS:
            add_item_to_db(
                stash['id'],
                stash['stash'],
                real_name,
                price,
                'chaos',
                stash.get('lastCharacterName'),
                item['league']
            )


while False:
    #delete_items_older_than_x_minutes(30)
    new_change_id, stashes = get_stash_data(change_id=change_id)
    for stash in stashes:
        delete_items_by_stash_id(stash['id'])

        if stash['public'] == 'false':
            continue

        if not stash.get('accountName', ''):
            continue

        parse_items(stash)

    if new_change_id:
        change_id = new_change_id

    time.sleep(.25)

    for item in WATCHED_ITEMS:
        find_underpriced_items(item)


