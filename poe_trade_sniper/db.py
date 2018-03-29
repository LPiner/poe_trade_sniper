import sqlite3
import time
from poe_trade_sniper.models import POEItem

DATABASE_NAME = 'poe_items.db'


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn


def add_item_to_db(stash_id: str, stash_name: str, item_name: str, price: float, price_units: str, username: str, league: str):
    conn = get_connection()
    c = conn.cursor()

    statement = "INSERT INTO items(stash_id, stash_name, item_name, price, price_units, user_name, league, timestamp) VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
    c.execute(statement, (stash_id, stash_name, item_name, price, price_units, username, league, time.time()))
    conn.commit()


def delete_items_by_stash_id(stash_id: str):
    conn = get_connection()
    c = conn.cursor()

    statement = "DELETE FROM items WHERE stash_id='%s'" % stash_id
    c.execute(statement)
    conn.commit()


def delete_items_older_than_x_minutes(minutes: int):
    conn = get_connection()
    c = conn.cursor()

    statement = "DELETE FROM items WHERE timestamp<'%s'" % (time.time() - (minutes * 60))
    c.execute(statement)
    conn.commit()


def find_items_by_name(item_name: str):
    conn = get_connection()
    c = conn.cursor()

    statement = "SELECT * FROM items where item_name=?"
    c.execute(statement, (item_name, ))

    records = c.fetchall()
    items = []
    for record in records:
        items.append(
            POEItem(id=record[0], stash_name=record[2], name=record[3], price=record[4], price_units=record[5]
                    , owner_name=record[6], league=record[8], alerted=record[7])

        )

    return items


def alert_item(item_id: int):
    conn = get_connection()
    c = conn.cursor()

    statement = "UPDATE items SET alerted=1 where id=?"
    c.execute(statement, (item_id,))
    conn.commit()


def init_sqlite3():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    create table if not exists items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stash_id TEXT,
        stash_name TEXT,
        item_name TEXT,
        price FLOAT,
        price_units TEXT,
        user_name TEXT,
        alerted BOOL DEFAULT 0,
        league TEXT,
        timestamp FLOAT
    )
    """)
    conn.commit()
    conn.close()


