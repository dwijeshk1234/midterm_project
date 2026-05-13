"""
init_db.py - Database initialization module for Dosa Restaurant API

Provides utilities to initialize SQLite database with proper schema including
customers, items, orders, and order_items tables with foreign key constraints.
"""

import sqlite3
from typing import None


def init_db() -> None:
    """
    
    Creates tables for customers, items, orders, and order_items with proper
    foreign key relationships and data validation constraints.
    
    Raises:
        sqlite3.OperationalError: If database creation fails
    """
    db_path: str = "db.sqlite"

    print(f"Setting up database at: {db_path}")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # --- CUSTOMERS TABLE ---
    # phone must be unique 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT    NOT NULL,
            phone TEXT    NOT NULL UNIQUE
        )
    """)

    # --- ITEMS TABLE ---
    # Stores the menu items (dosas, drinks)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT    NOT NULL UNIQUE,
            price REAL    NOT NULL CHECK(price >= 0)
        )
    """)

    # --- ORDERS TABLE ---
    # One row per order placed
    # customer_id links back to the customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   INTEGER NOT NULL,
            notes       TEXT    NOT NULL DEFAULT '',
            customer_id INTEGER NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # --- ORDER_ITEMS TABLE ---
    # Both order_id and item_id must point to real rows
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_id INTEGER NOT NULL,
            item_id  INTEGER NOT NULL,
            PRIMARY KEY (order_id, item_id),
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (item_id)  REFERENCES items(id)
        )
    """)

    conn.commit()
    conn.close()

    print("Done! Tables created: customers, items, orders, order_items")


if __name__ == "__main__":
    init_db()
