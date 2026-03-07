#!/usr/bin/env python3
"""
Flight Tracker Setup - Initialize SQLite database and schema
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "/Users/gerald/.openclaw/workspace/flight-tracker/flights.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS flights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_tracked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    departure_date TEXT,
    departure_time TEXT,
    arrival_time TEXT,
    duration TEXT,
    price INTEGER,
    airline TEXT,
    layovers INTEGER,
    layover_duration TEXT,
    departure_airport TEXT,
    arrival_airport TEXT,
    booking_url TEXT,
    UNIQUE(departure_date, departure_time, airline, price)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_tracked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    departure_date TEXT,
    best_price INTEGER,
    average_price INTEGER,
    price_std_dev REAL,
    flight_count INTEGER,
    UNIQUE(date_tracked, departure_date)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered TIMESTAMP,
    departure_date TEXT,
    price_threshold INTEGER,
    actual_price INTEGER,
    airline TEXT,
    status TEXT DEFAULT 'pending'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS amex_deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_tracked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    airline TEXT,
    program TEXT,
    round_trip_miles INTEGER,
    estimated_value_usd REAL,
    notes TEXT
)
""")

conn.commit()
conn.close()
print("✅ Database initialized at", DB_PATH)
