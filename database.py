import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            city TEXT,
            products TEXT,
            total REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            paid_at TEXT,
            delivered_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def create_order(user_id, username, city, products, total):
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (user_id, username, city, products, total, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, username, city, products, total, datetime.now().isoformat()))
    conn.commit()
    order_id = cur.lastrowid
    conn.close()
    return order_id

def update_order_status(order_id, status):
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()

def get_orders_by_status(status):
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE status = ?", (status,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_order(order_id):
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_user_orders(user_id):
    conn = sqlite3.connect("shop.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows