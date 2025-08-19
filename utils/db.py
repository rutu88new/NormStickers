import sqlite3
from pathlib import Path

DB_PATH = Path("data/state.sqlite")

def init():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""        CREATE TABLE IF NOT EXISTS processed (
            source TEXT,
            collection TEXT,
            item_id TEXT,
            url_hash TEXT,
            PRIMARY KEY (source, collection, item_id)
        )
    """)
    cur.execute("""        CREATE TABLE IF NOT EXISTS packs (
            source TEXT,
            collection TEXT,
            title TEXT,
            short_name TEXT,
            PRIMARY KEY (source, collection)
        )
    """)
    con.commit()
    con.close()

def remember_item(source, collection, item_id, url_hash):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO processed VALUES (?, ?, ?, ?)", (source, collection, item_id, url_hash))
    con.commit()
    con.close()

def is_seen(source, collection, item_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM processed WHERE source=? AND collection=? AND item_id=? LIMIT 1",
                (source, collection, item_id))
    row = cur.fetchone()
    con.close()
    return row is not None

def get_pack(source, collection):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT title, short_name FROM packs WHERE source=? AND collection=? LIMIT 1",
                (source, collection))
    row = cur.fetchone()
    con.close()
    return row if row else (None, None)

def save_pack(source, collection, title, short_name):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO packs VALUES (?, ?, ?, ?)", (source, collection, title, short_name))
    con.commit()
    con.close()
