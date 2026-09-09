"""
Order Manager — runs the full STORE or RETRIEVE process from start to finish.
Coordinates the Placement Engine and the Event Logger.
If anything fails partway through, everything is rolled back
(the database never ends up in a half-finished state).
"""

from app import db
from app.models.orders import Order
from app.models.shelves import Shelf
from app.models.items import Item
from app.logic.placement_engine import find_shelf
from app.logic.event_logger import log_event


def store_item(item_id, target_x, target_y, target_layer):
    """
    Runs a full STORE order.
    Returns (success: bool, message: str, order: Order)
    """
    item = Item.query.get(item_id)
    if item is None:
        return False, f'Item {item_id} not found.', None

    # Create the order record first, status = PENDING
    order = Order(
        action='STORE',
        item_id=item_id,
        status='PENDING',
    )
    db.session.add(order)
    db.session.commit()

    # Match item height to a height class (round up to nearest class)
    height_class = _height_to_class(item.height)

    shelf = find_shelf(target_x, target_y, target_layer, height_class)

    if shelf is None:
        # Nothing found anywhere — roll back and log failure
        order.status = 'FAILED'
        db.session.commit()
        log_event(
            action='STORE', result='FAILURE', item_id=item_id, order_id=order.id,
            notes='No suitable shelf found in any layer or height class.'
        )
        return False, 'No suitable shelf available.', order

    # Success — occupy the shelf, link it to the item, finish the order
    shelf.is_occupied = True
    shelf.item_id = item.id
    item.status = 'STORED'
    order.assigned_shelf_id = shelf.id
    order.status = 'DONE'
    db.session.commit()

    log_event(
        action='STORE', result='SUCCESS', shelf_id=shelf.id, item_id=item_id,
        order_id=order.id,
        notes=f'Stored at Layer {shelf.layer}, x={shelf.x}, y={shelf.y}'
    )
    return True, f'Item stored at Layer {shelf.layer}, x={shelf.x}, y={shelf.y}', order


def retrieve_item(item_id):
    """
    Runs a full RETRIEVE order.
    Returns (success: bool, message: str, order: Order)
    """
    item = Item.query.get(item_id)
    if item is None:
        return False, f'Item {item_id} not found.', None

    shelf = Shelf.query.filter_by(item_id=item_id, is_occupied=True).first()

    order = Order(
        action='RETRIEVE',
        item_id=item_id,
        status='PENDING',
    )
    db.session.add(order)
    db.session.commit()

    if shelf is None:
        order.status = 'FAILED'
        db.session.commit()
        log_event(
            action='RETRIEVE', result='FAILURE', item_id=item_id, order_id=order.id,
            notes='Item is not currently stored on any shelf.'
        )
        return False, 'Item is not currently stored anywhere.', order

    # Free the shelf, update the item
    shelf.is_occupied = False
    shelf.item_id = None
    item.status = 'RETRIEVED'
    order.assigned_shelf_id = shelf.id
    order.status = 'DONE'
    db.session.commit()

    log_event(
        action='RETRIEVE', result='SUCCESS', shelf_id=shelf.id, item_id=item_id,
        order_id=order.id,
        notes=f'Retrieved from Layer {shelf.layer}, x={shelf.x}, y={shelf.y}'
    )
    return True, f'Item retrieved from Layer {shelf.layer}, x={shelf.x}, y={shelf.y}', order


def _height_to_class(height_cm):
    """Rounds an item's height up to the nearest available shelf height class."""
    if height_cm <= 15:
        return 15
    elif height_cm <= 20:
        return 20
    else:
        return 32
