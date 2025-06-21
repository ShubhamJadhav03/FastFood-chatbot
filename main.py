from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app = FastAPI()

inprogress_orders = {}

@app.post("/")
async def handle_request(request: Request):
    try:
        payload = await request.json()
        intent = payload['queryResult']['intent']['displayName']
        print(f"[DEBUG] intent received: {intent}")
        parameters = payload['queryResult']['parameters']
        output_contexts = payload['queryResult'].get('outputContexts', [])
        session_id = generic_helper.extract_session_id(output_contexts[0]["name"]) if output_contexts else "unknown_session"

        intent_handler_dict = {
            'order.add - context: ongoing-order': add_to_order,
            'order.remove - context: ongoing-order': remove_from_order,
            'order.complete - context: ongoing-order': complete_order,
            'track.order -context: ongoing-tracking': track_order
        }

        handler = intent_handler_dict.get(intent)
        if not handler:
            return JSONResponse(content={"fulfillmentText": "Sorry, I didn't understand your request."})

        if handler.__code__.co_flags & 0x80:  # is async
            return await handler(parameters, session_id)
        else:
            return handler(parameters, session_id)

    except Exception as e:
        return JSONResponse(content={"fulfillmentText": f"Internal server error: {str(e)}"})


def save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()

    for food_item, quantity in order.items():
        item_id = db_helper.get_item_id(food_item)
        print(f"[DEBUG] food_item='{food_item}' => item_id={item_id}")
        if item_id is None:
            print(f"Could not find item ID for: {food_item}")
            return -1

        rcode = db_helper.insert_order_item(food_item, quantity, next_order_id)
        if rcode == -1:
            return -1

    db_helper.insert_order_tracking(next_order_id, "in progress")
    return next_order_id


def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having trouble finding your order. Please place a new one."
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)

        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. Please try again."
        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome. We have placed your order! " \
                               f"Order ID: {order_id}. Total: ₹{order_total}. Pay on delivery."

        del inprogress_orders[session_id]

    return JSONResponse(content={"fulfillmentText": fulfillment_text})


def add_to_order(parameters: dict, session_id: str):
    food_items = parameters.get("food-item", [])
    quantities = parameters.get("number", [])

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry, I didn't understand. Please clearly specify both food items and their quantities."
    else:
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            inprogress_orders[session_id].update(new_food_dict)
        else:
            inprogress_orders[session_id] = new_food_dict

        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})


def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={"fulfillmentText": "I couldn't find your order. Please place one first."})

    food_items = parameters.get("food-item", [])
    current_order = inprogress_orders[session_id]

    removed_items = []
    missing_items = []

    for item in food_items:
        if item in current_order:
            removed_items.append(item)
            del current_order[item]
        else:
            missing_items.append(item)

    fulfillment_parts = []

    if removed_items:
        fulfillment_parts.append(f"Removed: {', '.join(removed_items)}.")
    if missing_items:
        fulfillment_parts.append(f"{', '.join(missing_items)} were not in your order.")

    if not current_order:
        fulfillment_parts.append("Your order is now empty.")
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_parts.append(f"Current order: {order_str}.")

    fulfillment_text = " ".join(fulfillment_parts)
    return JSONResponse(content={"fulfillmentText": fulfillment_text})


def track_order(parameters: dict, session_id: str):
    order_id = parameters.get('order_id') or parameters.get('number')
    try:
        order_id = int(order_id)
    except (TypeError, ValueError):
        return JSONResponse(content={"fulfillmentText": "Please provide a valid numeric order ID."})

    order_status = db_helper.get_order_status(order_id)
    if order_status:
        fulfillment_text = f"Order ID {order_id} is currently: {order_status}."
    else:
        fulfillment_text = f"No order found with ID {order_id}."

    return JSONResponse(content={"fulfillmentText": fulfillment_text})
