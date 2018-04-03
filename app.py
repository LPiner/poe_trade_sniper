
from flask import Flask, render_template, jsonify, g
from werkzeug.contrib.cache import SimpleCache
from concurrent.futures import ThreadPoolExecutor
from sniper import *

init_sqlite3()

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=1)
cache = SimpleCache()
LEAGUE = 'Bestiary'

from poe_trade_sniper.currency import *
from poe_trade_sniper.db import *

def start_scraper():
    while True:
        parse_api()


def parse_api():

    start_time = time.time()
    try:

        change_id = get_latest_change_id()
        if not change_id:
            change_id = get_current_change_id()

        new_change_id, stashes = get_stash_data(change_id=change_id)

        if new_change_id:
            add_poe_api_result(change_id, new_change_id, [])

        updated_stashes = []
        for stash in stashes:
            updated_stashes.append(stash['id'])
        delete_items_in_stash_id_array(updated_stashes)

        for stash in stashes:

            if stash['public'] == 'false':
                continue

            if not stash.get('accountName', ''):
                continue

            parse_items(stash, LEAGUE)

    except Exception as e:
        logger.warn('Parser failed with error.', error=e)

    while time.time() - start_time < .5:
        time.sleep(.01)
    print(time.time() - start_time)

@app.route('/_get_predicted_trades')
def get_predicted_trades():


    items = []

    for item in WATCHED_ITEMS:
        items += find_underpriced_items(item)

    json_items = []
    for item in items:
        json_items.append(item.__dict__)

    return jsonify(items=json_items)


@app.route("/")
def index():
    return render_template('index.html')


if __name__ == '__main__':
    executor.submit(start_scraper)
    rates = get_currency_rates(LEAGUE)
    for rate in rates:
        add_currency_price(rate['currencyTypeName'], rate['chaosEquivalent'])
    add_currency_price('Chaos Orb', 1)
    app.run()
