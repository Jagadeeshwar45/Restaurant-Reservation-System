from db import init_db, load_restaurants, DB_PATH
from schema import Restaurant, Reservation
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
import json

init_db()
RESTAURANTS = {r['id']: Restaurant(**r) for r in load_restaurants()}

def search_restaurants(cuisine: Optional[str]=None, seats: Optional[int]=None, feature_filters: Optional[List[str]]=None, limit:int=20):
    results = list(RESTAURANTS.values())
    if cuisine:
        results = [r for r in results if r.cuisine.lower() == cuisine.lower()]
    if seats:
        results = [r for r in results if r.capacity >= seats]
    if feature_filters:
        results = [r for r in results if all(f in r.features for f in feature_filters)]
    return results[:limit]

def _get_conn():
    return sqlite3.connect(DB_PATH)

def check_availability(restaurant_id:int, dt:datetime, seats:int) -> bool:
    # Simple rule: count confirmed seats in a 2-hour window from dt hour-start
    conn = _get_conn()
    c = conn.cursor()
    window_start = dt.replace(minute=0, second=0, microsecond=0)
    window_end = window_start + timedelta(hours=2)
    c.execute('''
        SELECT COALESCE(SUM(seats),0) FROM reservations
        WHERE restaurant_id=? AND status='confirmed' AND datetime>=? AND datetime<? 
    ''', (restaurant_id, window_start.isoformat(), window_end.isoformat()))
    booked = c.fetchone()[0] or 0
    conn.close()
    cap = RESTAURANTS[restaurant_id].capacity
    return (booked + seats) <= cap

def create_reservation(restaurant_id:int, dt:datetime, seats:int, name:str, phone:Optional[str]=None, email:Optional[str]=None):
    if not check_availability(restaurant_id, dt, seats):
        return None
    conn = _get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO reservations (restaurant_id, datetime, seats, name, phone, email, status)
        VALUES (?, ?, ?, ?, ?, ?, 'confirmed')
    ''', (restaurant_id, dt.isoformat(), seats, name, phone, email))
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return Reservation(id=rid, restaurant_id=restaurant_id, datetime=dt, seats=seats, name=name, phone=phone, email=email)

def cancel_reservation(reservation_id:int) -> bool:
    conn = _get_conn()
    c = conn.cursor()
    c.execute('SELECT id FROM reservations WHERE id=?', (reservation_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    c.execute('UPDATE reservations SET status="cancelled" WHERE id=?', (reservation_id,))
    conn.commit()
    conn.close()
    return True

def list_reservations():
    conn = _get_conn()
    c = conn.cursor()
    c.execute('SELECT id, restaurant_id, datetime, seats, name, phone, email, status FROM reservations ORDER BY id DESC LIMIT 200')
    rows = c.fetchall()
    conn.close()
    results = []
    for r in rows:
        results.append({
            'id': r[0],
            'restaurant_id': r[1],
            'datetime': r[2],
            'seats': r[3],
            'name': r[4],
            'phone': r[5],
            'email': r[6],
            'status': r[7]
        })
    return results
