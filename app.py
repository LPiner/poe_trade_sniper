
from flask import Flask, render_template, jsonify
from sniper import *
from concurrent.futures import ThreadPoolExecutor

from poe_trade_sniper.db import init_sqlite3, add_item_to_db, delete_items_by_stash_id, delete_items_older_than_x_minutes, find_items_by_name, alert_item

app = Flask(__name__)
executor = ThreadPoolExecutor(2)
init_sqlite3()


def start_scraper():
    executor.submit(parse_api)


def parse_api(change_id=None):
    if not change_id:
        change_id = get_current_change_id()

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

    time.sleep(.3)

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
    app.run(debug=1)
