import sqlite3
import time
import json
from poe_trade_sniper.models import POEItem

DATABASE_NAME = 'poe_items.db'


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn


def add_item_to_db(stash_id: str, stash_name: str, item_name: str, price: float, price_units: str, price_in_chaos, username: str, league: str):
    conn = get_connection()
    c = conn.cursor()

    statement = "INSERT INTO items(stash_id, stash_name, item_name, price, price_units, price_in_chaos, user_name, league, timestamp) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
    c.execute(statement, (stash_id, stash_name, item_name, price, price_units, price_in_chaos, username, league, time.time()))
    conn.commit()


def delete_items_by_stash_id(stash_id: str):
    conn = get_connection()
    c = conn.cursor()

    statement = "DELETE FROM items WHERE stash_id='%s'" % stash_id
    c.execute(statement)
    conn.commit()

def delete_items_in_stash_id_array(stash_ids: list):
    conn = get_connection()
    c = conn.cursor()

    statement = "DELETE FROM items WHERE 'stash_id' IN ({seq})".format(
        seq=','.join(['?']*len(stash_ids)))
    c.execute(statement, stash_ids)
    conn.commit()



def delete_items_older_than_x_minutes(minutes: int):
    conn = get_connection()
    c = conn.cursor()

    statement = "DELETE FROM items WHERE timestamp<'%s'" % (time.time() - (minutes * 60))
    c.execute(statement)
    conn.commit()


def delete_all_currency_prices():
    conn = get_connection()
    c = conn.cursor()

    statement = "DELETE FROM currency_prices"
    c.execute(statement)
    conn.commit()


def add_currency_price(currency: str, chaos_price: float):
    conn = get_connection()
    c = conn.cursor()

    statement = "INSERT INTO currency_prices(currency, price_in_chaos, timestamp) VALUES(?, ?, ?)"
    c.execute(statement, (currency, chaos_price, time.time()))
    conn.commit()


def get_currency_price(currency: str):
    conn = get_connection()
    c = conn.cursor()

    statement = "SELECT * FROM currency_prices where currency=?"
    c.execute(statement, (currency,))

    records = c.fetchone()
    return records


def find_items_by_name(item_name: str):
    conn = get_connection()
    c = conn.cursor()

    statement = "SELECT rowid, * FROM items where item_name=?"
    c.execute(statement, (item_name, ))

    records = c.fetchall()
    items = []
    for record in records:
        items.append(
            POEItem(id=record[0], stash_name=record[2], name=record[3], price=record[4], price_units=record[5]
                    , owner_name=record[7], league=record[9], alerted=record[8], price_in_chaos=record[6])

        )

    return items


def add_poe_api_result(change_id: str, next_change_id: str, stash_data: list):
    conn = get_connection()
    c = conn.cursor()

    statement = "INSERT INTO poe_api_results(change_id, next_change_id, stash_data, timestamp) VALUES(?, ?, ?, ?)"
    c.execute(statement, (change_id, next_change_id, json.dumps(stash_data), time.time()))
    conn.commit()


def get_latest_change_id() -> str:
    conn = get_connection()
    c = conn.cursor()

    statement = "SELECT next_change_id FROM poe_api_results WHERE rowid = (SELECT MAX(rowid) FROM poe_api_results);"
    c.execute(statement)
    record = c.fetchone()
    if not record:
        return ''
    return record[0]



def alert_item(item_id: int):
    conn = get_connection()
    c = conn.cursor()

    statement = "UPDATE items SET alerted=1 where rowid=?"
    c.execute(statement, (item_id,))
    conn.commit()


def init_sqlite3():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    create table if not exists items (
        stash_id TEXT,
        stash_name TEXT,
        item_name TEXT,
        price FLOAT,
        price_units TEXT,
        price_in_chaos FLOAT,
        user_name TEXT,
        alerted BOOL DEFAULT 0,
        league TEXT,
        timestamp FLOAT
    )
    """)
    conn.commit()

    c.execute("""
    create table if not exists currency_prices (
        currency TEXT,
        price_in_chaos FLOAT,
        timestamp FLOAT
    )
    """)
    conn.commit()

    c.execute("""
    create table if not exists poe_api_results (
        change_id TEXT,
        next_change_id TEXT,
        stash_data TExt,
        timestamp FLOAT
    )
    """)
    conn.commit()
    c.execute("""
    CREATE INDEX IF NOT EXISTS item_names ON items (item_name)
    """)
    conn.commit()
    conn.close()


