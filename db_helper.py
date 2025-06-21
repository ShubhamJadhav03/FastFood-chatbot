# db_helper.py

import mysql.connector
from mysql.connector import Error, OperationalError

# Global connection
cnx = None

def connect_db():
    global cnx
    if cnx is None or not cnx.is_connected():
        cnx = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="pandeyji_eatery"
        )

def insert_order_item(food_name, quantity, order_id):
    try:
        connect_db()
        cursor = cnx.cursor()
        cursor.callproc('insert_order_item', (food_name, quantity, order_id))
        print(f"[DEBUG] Inserting: food_name={food_name}, quantity={quantity}, order_id={order_id}")
        cnx.commit()
        cursor.close()
        print("Order item inserted successfully!")
        return 1
    except Error as err:
        print(f"Error inserting order item: {err}")
        cnx.rollback()
        return -1


def get_item_id(food_name: str):
    try:
        connect_db()
        cursor = cnx.cursor()
        cursor.execute("SELECT item_id FROM food_items WHERE LOWER(name) = %s", (food_name.lower(),))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Error as err:
        print(f"Error fetching item_id for '{food_name}': {err}")
        return None


def insert_order_tracking(order_id: int, status: str):
    try:
        connect_db()
        cursor = cnx.cursor()
        cursor.execute(
            "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)", (order_id, status)
        )
        cnx.commit()
        cursor.close()
    except Error as err:
        print(f"Error inserting order tracking: {err}")
        cnx.rollback()


def get_total_order_price(order_id: int):
    try:
        connect_db()
        cursor = cnx.cursor()
        cursor.execute("SELECT get_total_order_price(%s)", (order_id,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Error as err:
        print(f"Error getting total order price: {err}")
        return None


def get_next_order_id():
    try:
        connect_db()
        cursor = cnx.cursor()
        cursor.execute("SELECT MAX(order_id) FROM orders")
        result = cursor.fetchone()[0]
        cursor.close()
        return 1 if result is None else result + 1
    except Error as err:
        print(f"Error getting next order ID: {err}")
        return -1


def get_order_status(order_id: int):
    try:
        connect_db()
        cursor = cnx.cursor()
        cursor.execute("SELECT status FROM order_tracking WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Error as err:
        print(f"Error getting order status: {err}")
        return None
