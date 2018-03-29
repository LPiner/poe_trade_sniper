
from flask import Flask, render_template, jsonify, g
from werkzeug.contrib.cache import SimpleCache
from concurrent.futures import ThreadPoolExecutor
from sniper import *

init_sqlite3()

app = Flask(__name__)
executor = ThreadPoolExecutor(2)
cache = SimpleCache()
LEAGUE = 'Bestiary'

from poe_trade_sniper.currency import *
from poe_trade_sniper.db import *

def start_scraper():
    parse_api()


def parse_api(change_id=None):

    try:

        if not change_id:
            change_id = get_current_change_id()

        new_change_id, stashes = get_stash_data(change_id=change_id)
        for stash in stashes:
            delete_items_by_stash_id(stash['id'])

            if stash['public'] == 'false':
                continue

            if not stash.get('accountName', ''):
                continue

            parse_items(stash, LEAGUE)

        if new_change_id:
            change_id = new_change_id

    except Exception as e:
        logger.warn('Parser failed with error.', error=e)
    time.sleep(.4)
    executor.submit(parse_api, change_id)


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
    start_scraper()
    rates = get_currency_rates(LEAGUE)
    for rate in rates:
        add_currency_price(rate['currencyTypeName'], rate['chaosEquivalent'])
    add_currency_price('Chaos Orb', 1)
    app.run(debug=1)
