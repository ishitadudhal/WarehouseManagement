from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__)

# Input limits (from System_Architecture.docx section 2.6)
VALID_ROWS   = range(1, 8)   # x: 1–7
VALID_COLS   = range(1, 9)   # y: 1–8
VALID_LAYERS = (1, 2)
VALID_HEIGHT_CLASSES = (15, 20, 32)


# ── Shelves ───────────────────────────────────────────────────────────────────

@api_bp.route('/shelves', methods=['GET'])
def get_shelves():
    """Return all shelf positions and their current state."""
    from app.models.shelves import Shelf
    shelves = Shelf.query.all()
    return jsonify([s.to_dict() for s in shelves])


# ── Items ─────────────────────────────────────────────────────────────────────

@api_bp.route('/items', methods=['GET'])
def get_items():
    """Return all registered items."""
    from app.models.items import Item
    items = Item.query.all()
    return jsonify([i.to_dict() for i in items])


@api_bp.route('/items', methods=['POST'])
def create_item():
    """
    Register a new item.
    Body: { "name": "Box A", "height": 18, "width": 20, "depth": 20, "weight": 3.5 }
    """
    from app import db
    from app.models.items import Item

    data = request.get_json(silent=True) or {}
    name   = data.get('name')
    height = data.get('height')
    width  = data.get('width')
    depth  = data.get('depth')
    weight = data.get('weight')

    if not name or height is None or width is None or depth is None:
        return jsonify({'error': 'name, height, width and depth are required.'}), 400

    item = Item(name=name, height=height, width=width, depth=depth, weight=weight)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


# ── Orders ────────────────────────────────────────────────────────────────────

@api_bp.route('/orders/store', methods=['POST'])
def store_item_route():
    """
    Store an item in the warehouse.
    Body: { "item_id": 1, "target_x": 3, "target_y": 4, "target_layer": 1 }
    """
    from app.logic.order_manager import store_item
    from app.logic.event_logger import log_event

    data = request.get_json(silent=True) or {}
    item_id      = data.get('item_id')
    target_x     = data.get('target_x')
    target_y     = data.get('target_y')
    target_layer = data.get('target_layer')

    # Validate input before it reaches the business logic
    error = _validate_store_request(item_id, target_x, target_y, target_layer)
    if error:
        log_event(action='VALIDATION_ERROR', result='FAILURE', item_id=item_id, notes=error)
        return jsonify({'error': error}), 400

    success, message, order = store_item(item_id, target_x, target_y, target_layer)
    status_code = 200 if success else 409
    return jsonify({
        'success': success,
        'message': message,
        'order': order.to_dict() if order else None,
    }), status_code


@api_bp.route('/orders/retrieve', methods=['POST'])
def retrieve_item_route():
    """
    Retrieve an item from the warehouse.
    Body: { "item_id": 1 }
    """
    from app.logic.order_manager import retrieve_item
    from app.logic.event_logger import log_event

    data = request.get_json(silent=True) or {}
    item_id = data.get('item_id')

    if not isinstance(item_id, int):
        error = 'item_id is required and must be an integer.'
        log_event(action='VALIDATION_ERROR', result='FAILURE', notes=error)
        return jsonify({'error': error}), 400

    success, message, order = retrieve_item(item_id)
    status_code = 200 if success else 409
    return jsonify({
        'success': success,
        'message': message,
        'order': order.to_dict() if order else None,
    }), status_code


# ── Events ────────────────────────────────────────────────────────────────────

@api_bp.route('/events', methods=['GET'])
def get_events():
    """Return the last 50 events (newest first)."""
    from app.models.events import Event
    events = Event.query.order_by(Event.timestamp.desc()).limit(50).all()
    return jsonify([e.to_dict() for e in events])


# ── Validation helper ─────────────────────────────────────────────────────────

def _validate_store_request(item_id, target_x, target_y, target_layer):
    """Returns an error message string if invalid, or None if the request is OK."""
    if not isinstance(item_id, int):
        return 'item_id is required and must be an integer.'
    if not isinstance(target_x, int) or target_x not in VALID_ROWS:
        return f'target_x must be an integer between {VALID_ROWS.start} and {VALID_ROWS.stop - 1}.'
    if not isinstance(target_y, int) or target_y not in VALID_COLS:
        return f'target_y must be an integer between {VALID_COLS.start} and {VALID_COLS.stop - 1}.'
    if target_layer not in VALID_LAYERS:
        return f'target_layer must be one of {VALID_LAYERS}.'
    return None
