# Dosa Restaurant API

**Student:** Dwijesh K
**Course:** NJIT CS490 Python Web API
**Final Project**

\---

## What this is

A backend REST API for a dosa restaurant. You can create customers, add menu items, and place orders. Everything is saved to a SQLite database file on your computer. There is no frontend — test everything through the browser at `/docs` or using curl commands.---

## How the data connects

There are 4 tables. Here is how they relate:

* A **customer** can have many **orders**
* An **order** belongs to one **customer**
* An **order** can have many **items** (like ordering two dosas at once)
* The **order\_items** table sits in the middle connecting orders and items

So if we delete a customer, we have to delete their orders first. The database will block we otherwise because of the foreign key constraint.

\---

## Setup

we need Python 3.10 or newer.

Install the two required packages:

```
pip install fastapi uvicorn
```

Then create the database. Run this once:

```
python init\_db.py
```

we should see:

```
Setting up database at: db.sqlite
Done! Tables created: customers, items, orders, order\_items
```

Then start the server:

```
uvicorn main:app --reload
```

Open wer browser and go to `http://127.0.0.1:8000/docs` — that page lets we click and test every endpoint without typing any curl commands.

\---

## Endpoints

### Customers

|Method|Path|What it does|
|-|-|-|
|POST|`/customers`|Add a new customer|
|GET|`/customers/{id}`|Look up a customer by ID|
|PUT|`/customers/{id}`|Update a customer's name or phone|
|DELETE|`/customers/{id}`|Remove a customer|

```json
{ "name": "Durga", "phone": "732-555-0101" }
```

### Items

|Method|Path|What it does|
|-|-|-|
|POST|`/items`|Add a menu item|
|GET|`/items/{id}`|Look up an item by ID|
|PUT|`/items/{id}`|Update an item's name or price|
|DELETE|`/items/{id}`|Remove a menu item|

```json
{ "name": "Masala Dosa", "price": 10.95 }
```

### Orders

|Method|Path|What it does|
|-|-|-|
|POST|`/orders`|Place a new order|
|GET|`/orders/{id}`|Look up an order by ID|
|PUT|`/orders/{id}`|Update an order|
|DELETE|`/orders/{id}`|Cancel/remove an order|

```json
{
  "customer\_id": 1,
  "item\_ids": \[1, 2],
  "notes": "extra spicy",
  "timestamp": 1702219784
}
```

`timestamp` is optional. If we leave it out, it uses the current time.

\---

## Testing from terminal (Windows)

The server needs to be running first (`uvicorn main:app --reload`).

**Create a customer:**

```
curl -X POST http://127.0.0.1:8000/customers -H "Content-Type: application/json" -d "{\\"name\\": \\"Durga\\", \\"phone\\": \\"732-555-0101\\"}"
```

**Get that customer:**

```
curl http://127.0.0.1:8000/customers/1
```

**Update the customer:**

```
curl -X PUT http://127.0.0.1:8000/customers/1 -H "Content-Type: application/json" -d "{\\"name\\": \\"Durga\\", \\"phone\\": \\"732-555-9999\\"}"
```

**Delete the customer:**

```
curl -X DELETE http://127.0.0.1:8000/customers/1
```

**Create a menu item:**

```
curl -X POST http://127.0.0.1:8000/items -H "Content-Type: application/json" -d "{\\"name\\": \\"Masala Dosa\\", \\"price\\": 10.95}"
```

**Create an order** (customer and item must exist first):

```
curl -X POST http://127.0.0.1:8000/orders -H "Content-Type: application/json" -d "{\\"customer\_id\\": 1, \\"item\_ids\\": \[1], \\"notes\\": \\"extra spicy\\"}"
```

**Get the order:**

```
curl http://127.0.0.1:8000/orders/1
```

**Delete the order:**

```
curl -X DELETE http://127.0.0.1:8000/orders/1
```

The right order to test: create a customer first, then an item, then an order that uses both.

\---

## Errors the API returns

|What went wrong|Error code|Message|
|-|-|-|
|ID does not exist|404|"No customer/item/order found with id=X"|
|Phone number already used|409|"Phone number already taken"|
|Item name already exists|409|"Item already exists"|
|Order points to missing customer|404|"Customer does not exist"|
|Order points to missing item|404|"Item does not exist"|
|Blank name or phone sent|422|"name cannot be blank"|
|Negative price sent|422|"price cannot be negative"|
|Order sent with no items|422|"order must have at least one item"|
|init\_db.py was never run|500|"Did we run init\_db.py first?"|

\---

## Known limitations

* Deleting a customer will fail if they have orders. Delete the orders first.
* There is no authentication — anyone who can reach the server can read and change everything.
* The database is a single file (`db.sqlite`) on we computer. If we delete it, all data is gone.
* No way to list all customers or all items right now — we can only fetch by ID.

