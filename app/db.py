import sqlite3
from pathlib import Path
from datetime import datetime
import json

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
DB_PATH = DATA_DIR / 'reservations.db'
RESTAURANTS_JSON = DATA_DIR / 'restaurants.json'

def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER,
            datetime TEXT,
            seats INTEGER,
            name TEXT,
            phone TEXT,
            email TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_restaurants():
    with open(RESTAURANTS_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)
