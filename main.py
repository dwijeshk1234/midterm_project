"""
main.py

The restaurant API server. Handles customers, items, and orders.

"""

import sqlite3
import time
from contextlib import contextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator



app = FastAPI(title="Dosa Restaurant API")

DB_FILE = "db.sqlite"

@contextmanager
def get_db():

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except sqlite3.OperationalError as e:
        # This usually means init_db.py was never run
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}. Did you run init_db.py first?"
        )
    finally:
        conn.close()


# --- CUSTOMER ---

class CustomerIn(BaseModel):
    """What you send when creating or updating a customer."""
    name: str
    phone: str

    @field_validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("name cannot be blank")
        return v.strip()

    @field_validator("phone")
    def phone_not_empty(cls, v):
        if not v.strip():
            raise ValueError("phone cannot be blank")
        return v.strip()


class CustomerOut(BaseModel):
    """What you get back after reading a customer."""
    id: int
    name: str
    phone: str


# --- ITEM ---

class ItemIn(BaseModel):
    """What you send when creating or updating a menu item."""
    name: str
    price: float

    @field_validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("name cannot be blank")
        return v.strip()

    @field_validator("price")
    def price_is_positive(cls, v):
        if v < 0:
            raise ValueError("price cannot be negative")
        return v


class ItemOut(BaseModel):
    """What you get back after reading a menu item."""
    id: int
    name: str
    price: float


# --- ORDER ---

class OrderIn(BaseModel):
    """What you send when creating or updating an order."""
    customer_id: int
    item_ids: List[int]          
    notes: Optional[str] = ""
    timestamp: Optional[int] = None   

    @field_validator("item_ids")
    def at_least_one_item(cls, v):
        if not v:
            raise ValueError("order must have at least one item")
        return v

    @field_validator("customer_id")
    def customer_id_positive(cls, v):
        if v <= 0:
            raise ValueError("customer_id must be a positive number")
        return v


class OrderOut(BaseModel):
    """What you get back after reading an order."""
    id: int
    timestamp: int
    notes: str
    customer_id: int
    item_ids: List[int]



def fetch_order_by_id(conn, order_id: int):

    row = conn.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()

    if row is None:
        return None

    item_rows = conn.execute(
        "SELECT item_id FROM order_items WHERE order_id = ?", (order_id,)
    ).fetchall()

    order = dict(row)
    order["item_ids"] = [r["item_id"] for r in item_rows]
    return order


def check_customer_exists(conn, customer_id: int):
    """Raises a 404 error if the customer doesn't exist."""
    row = conn.execute(
        "SELECT id FROM customers WHERE id = ?", (customer_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Customer with id={customer_id} does not exist"
        )


def check_item_exists(conn, item_id: int):
    """Raises a 404 error if the item doesn't exist."""
    row = conn.execute(
        "SELECT id FROM items WHERE id = ?", (item_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Item with id={item_id} does not exist"
        )


@app.post("/customers", response_model=CustomerOut, status_code=201)
def create_customer(body: CustomerIn):
    with get_db() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO customers (name, phone) VALUES (?, ?)",
                (body.name, body.phone)
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=f"Phone number '{body.phone}' is already taken by another customer"
            )

        return {"id": cursor.lastrowid, "name": body.name, "phone": body.phone}


@app.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int):
    """
    Get one customer by their ID.
    Fails with 404 if they don't exist.
    """
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No customer found with id={customer_id}"
        )

    return dict(row)


@app.put("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, body: CustomerIn):

    with get_db() as conn:
        # First make sure they exist
        existing = conn.execute(
            "SELECT id FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail=f"No customer found with id={customer_id}"
            )

        try:
            conn.execute(
                "UPDATE customers SET name = ?, phone = ? WHERE id = ?",
                (body.name, body.phone, customer_id)
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=f"Phone number '{body.phone}' is already taken by another customer"
            )

    return {"id": customer_id, "name": body.name, "phone": body.phone}


@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int):
    """
    Delete a customer.
    Fails with 404 if they don't exist.
    Note: you should delete their orders first, or this may fail due to FK constraints.
    """
    with get_db() as conn:
        result = conn.execute(
            "DELETE FROM customers WHERE id = ?", (customer_id,)
        )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No customer found with id={customer_id}"
        )

    return {"message": f"Customer {customer_id} deleted successfully"}


# ──────────────────────────────────────────────
# ITEM ENDPOINTS
# ──────────────────────────────────────────────

@app.post("/items", response_model=ItemOut, status_code=201)
def create_item(body: ItemIn):
    """
    Add a new menu item.
    Fails if an item with the same name already exists.
    """
    with get_db() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO items (name, price) VALUES (?, ?)",
                (body.name, body.price)
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=f"An item called '{body.name}' already exists"
            )

        return {"id": cursor.lastrowid, "name": body.name, "price": body.price}


@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int):
    """
    Get one menu item by its ID.
    Fails with 404 if it doesn't exist.
    """
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM items WHERE id = ?", (item_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No item found with id={item_id}"
        )

    return dict(row)


@app.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, body: ItemIn):
    """
    Update a menu item's name and/or price.
    Fails with 404 if the item doesn't exist.
    Fails with 409 if the new name is already used by another item.
    """
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail=f"No item found with id={item_id}"
            )

        try:
            conn.execute(
                "UPDATE items SET name = ?, price = ? WHERE id = ?",
                (body.name, body.price, item_id)
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=f"An item called '{body.name}' already exists"
            )

    return {"id": item_id, "name": body.name, "price": body.price}


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    """
    Delete a menu item.
    Fails with 404 if it doesn't exist.
    """
    with get_db() as conn:
        result = conn.execute(
            "DELETE FROM items WHERE id = ?", (item_id,)
        )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No item found with id={item_id}"
        )

    return {"message": f"Item {item_id} deleted successfully"}




@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(body: OrderIn):

    ts = body.timestamp if body.timestamp is not None else int(time.time())

    with get_db() as conn:
        check_customer_exists(conn, body.customer_id)

        for item_id in body.item_ids:
            check_item_exists(conn, item_id)

        # Insert the order
        cursor = conn.execute(
            "INSERT INTO orders (timestamp, notes, customer_id) VALUES (?, ?, ?)",
            (ts, body.notes or "", body.customer_id)
        )
        order_id = cursor.lastrowid

        # Link each item to this order
        for item_id in body.item_ids:
            conn.execute(
                "INSERT INTO order_items (order_id, item_id) VALUES (?, ?)",
                (order_id, item_id)
            )

    return {
        "id": order_id,
        "timestamp": ts,
        "notes": body.notes or "",
        "customer_id": body.customer_id,
        "item_ids": body.item_ids
    }


@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int):

    with get_db() as conn:
        order = fetch_order_by_id(conn, order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail=f"No order found with id={order_id}"
        )

    return order


@app.put("/orders/{order_id}", response_model=OrderOut)
def update_order(order_id: int, body: OrderIn):
    """
    Update an order — change customer, items, notes, or timestamp.

    Fails if:
    - the order doesn't exist
    - the new customer doesn't exist
    - any of the new item IDs don't exist
    """
    ts = body.timestamp if body.timestamp is not None else int(time.time())

    with get_db() as conn:
        # Make sure the order actually exists
        if fetch_order_by_id(conn, order_id) is None:
            raise HTTPException(
                status_code=404,
                detail=f"No order found with id={order_id}"
            )

        # Make sure the customer exists
        check_customer_exists(conn, body.customer_id)

        # Make sure all items exist
        for item_id in body.item_ids:
            check_item_exists(conn, item_id)

        # Update the order row
        conn.execute(
            "UPDATE orders SET timestamp = ?, notes = ?, customer_id = ? WHERE id = ?",
            (ts, body.notes or "", body.customer_id, order_id)
        )

        # Remove old item links and add the new ones
        conn.execute(
            "DELETE FROM order_items WHERE order_id = ?", (order_id,)
        )
        for item_id in body.item_ids:
            conn.execute(
                "INSERT INTO order_items (order_id, item_id) VALUES (?, ?)",
                (order_id, item_id)
            )

    return {
        "id": order_id,
        "timestamp": ts,
        "notes": body.notes or "",
        "customer_id": body.customer_id,
        "item_ids": body.item_ids
    }


@app.delete("/orders/{order_id}")
def delete_order(order_id: int):

    with get_db() as conn:
        # Check it exists first
        if fetch_order_by_id(conn, order_id) is None:
            raise HTTPException(
                status_code=404,
                detail=f"No order found with id={order_id}"
            )

        # Delete the item links first (FK constraint requires this order)
        conn.execute(
            "DELETE FROM order_items WHERE order_id = ?", (order_id,)
        )

        # Now delete the order itself
        conn.execute(
            "DELETE FROM orders WHERE id = ?", (order_id,)
        )

    return {"message": f"Order {order_id} deleted successfully"}
