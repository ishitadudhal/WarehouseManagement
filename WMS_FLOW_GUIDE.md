# Warehouse Management System: Complete Flow Guide

This document describes the code that currently exists in this repository. It separates implemented behavior from ideas that appear in `WMS_Build_Roadmap.html` but are not implemented yet.

## 1. What the system is

The project is a Flask web application for tracking warehouse shelf positions, registered items, store and retrieve orders, and an append-only event history.

The current runtime is an API-only backend:

```text
Client (Postman, frontend, or another service)
                    |
                    v
          Flask API: /api/v1/*
                    |
        +-----------+------------+
        |                        |
        v                        v
  Order Manager            Direct queries
        |                (shelves/items/events)
        v
 Placement Engine + Event Logger
        |
        v
 SQLite database: instance/wms.db
```

The OPC UA machine adapter exists as a separate module, but the store/retrieve API does not call it yet. The dashboard, authentication routes, and frontend JavaScript are also not present in the current repository.

## 2. Repository map

```text
WMS/
  run.py                         Application entry point
  seed_shelves.py                One-time shelf data generator
  requirements.txt               Python dependencies
  app/
    __init__.py                  Flask app factory and extensions
    api/routes.py                HTTP endpoints and input validation
    logic/order_manager.py       Store/retrieve orchestration
    logic/placement_engine.py    Shelf-selection algorithm
    logic/event_logger.py        Audit-event writer
    logic/machine_interface.py   OPC UA adapter for the physical machine
    models/items.py              Item table and serialization
    models/shelves.py            Shelf table and serialization
    models/orders.py              Order table and serialization
    models/events.py              Event table and serialization
    models/__init__.py           Imports all models for table creation
  instance/                      SQLite database location
  templates/                     Currently empty
  static/js/                     Currently empty
```

`WMS_Build_Roadmap.html` is planning material. It describes desired future work, but it is not part of the Flask request flow.

## 3. Startup flow

### Step 1: Python loads `run.py`

`run.py` performs three important actions:

1. Imports `create_app` from `app`.
2. Imports `app.models`. This causes `Shelf`, `Item`, `Order`, and `Event` to be imported before table creation.
3. Calls `create_app()` and stores the result in `flask_app`.

When the file is executed directly, Flask starts its development server on `http://127.0.0.1:5000` with debug mode enabled.

### Step 2: `create_app()` builds the Flask application

`app/__init__.py` creates a Flask instance with:

- `templates/` as the template folder
- `static/` as the static folder
- a hard-coded development secret key
- SQLite at `sqlite:///../instance/wms.db`
- SQLAlchemy tracking disabled

The `db` SQLAlchemy extension is attached to the app. Flask-Login is also initialized and configured with `auth.login` as its login endpoint, although no `auth` blueprint or login route currently exists.

### Step 3: API registration

`app.api.routes.api_bp` is registered with the prefix `/api/v1`. Therefore the route declared as `/items` is reached at `/api/v1/items`.

### Step 4: Tables are created

Inside an application context, `db.create_all()` creates missing tables based on the imported models. This creates tables; it does not migrate existing tables when model definitions change.

The first application startup can therefore create the SQLite file and schema. Shelf rows are not created automatically; that requires the separate seed script.

## 4. Database model and relationships

### `items`

One row represents one registered physical item.

| Field | Meaning |
|---|---|
| `id` | Primary key |
| `name` | Required item name |
| `height` | Height in centimeters |
| `width` | Width in centimeters |
| `depth` | Depth in centimeters |
| `weight` | Optional weight in kilograms |
| `status` | `REGISTERED`, `STORED`, or `RETRIEVED` |
| `created_at` | UTC creation timestamp |

An item has many orders through the `Item.orders` back-reference. A shelf can refer to the item currently occupying it through `Shelf.item`.

### `shelves`

One row represents one physical shelf position.

| Field | Meaning |
|---|---|
| `id` | Primary key |
| `x` | Warehouse row, normally 1 through 7 |
| `y` | Warehouse column, normally 1 through 8 |
| `layer` | Layer 1 or 2 |
| `height_class` | Shelf capacity class: 15, 20, or 32 cm |
| `is_occupied` | Whether an item is currently assigned |
| `item_id` | Nullable foreign key to the occupying item |

The model does not contain the `is_addressable` column mentioned by the roadmap. The placement engine consequently considers every seeded shelf row addressable.

### `orders`

One row represents one store or retrieve instruction.

| Field | Meaning |
|---|---|
| `id` | Primary key |
| `action` | `STORE` or `RETRIEVE` |
| `item_id` | Item being acted on |
| `target_shelf_id` | Intended shelf; currently never populated by the API flow |
| `assigned_shelf_id` | Shelf actually used |
| `status` | `PENDING`, `IN_PROGRESS`, `DONE`, or `FAILED` |
| `created_at` | Creation timestamp |
| `completed_at` | Nullable completion timestamp; currently never set |

### `events`

One row is an audit record. It stores the action, result, optional references to a shelf/item/order, notes, and a UTC timestamp. The logger appends rows, but the database schema does not itself enforce immutability.

## 5. Shelf seeding flow

Run the script from inside `WMS` after the application has created the database:

```powershell
python seed_shelves.py
```

The script:

1. Creates the app, which also ensures the tables exist.
2. Checks `Shelf.query.count()`.
3. Stops without changes if any shelf row already exists.
4. Otherwise loops over layers `1, 2`, rows `x=1..7`, and columns `y=1..8`.
5. Assigns height classes by row:
   - rows 1 and 2: 32 cm
   - rows 3, 4, and 5: 20 cm
   - rows 6 and 7: 15 cm
6. Inserts and commits all generated rows.

That produces 2 x 7 x 8 = 112 shelf rows. Some comments in the repository say 200, but the code actually creates 112.

## 6. API flow

### GET `/api/v1/shelves`

The route queries every shelf and serializes each row with `Shelf.to_dict()`.

Example response shape:

```json
[
  {
    "id": 1,
    "x": 1,
    "y": 1,
    "layer": 1,
    "height_class": 32,
    "is_occupied": false,
    "item_id": null
  }
]
```

### GET `/api/v1/items`

The route queries all items and returns their serialized physical properties, status, and ISO-formatted creation timestamp.

### POST `/api/v1/items`

Request body:

```json
{
  "name": "Box A",
  "height": 18,
  "width": 20,
  "depth": 20,
  "weight": 3.5
}
```

The route reads JSON, requires `name`, `height`, `width`, and `depth`, creates an `Item`, commits it, and returns HTTP 201 with the serialized item. `weight` is optional. The route does not currently validate positive dimensions, maximum height, numeric types, or duplicate names.

### POST `/api/v1/orders/store`

Request body:

```json
{
  "item_id": 1,
  "target_x": 3,
  "target_y": 4,
  "target_layer": 1
}
```

The route validates:

- `item_id` is an integer
- `target_x` is 1 through 7
- `target_y` is 1 through 8
- `target_layer` is 1 or 2

Invalid input is logged as a `VALIDATION_ERROR` event and returns HTTP 400. Valid input is passed to `order_manager.store_item()`.

The business result is returned as:

```json
{
  "success": true,
  "message": "Item stored at Layer 1, x=3, y=4",
  "order": {
    "id": 1,
    "action": "STORE",
    "item_id": 1,
    "target_shelf_id": null,
    "assigned_shelf_id": 20,
    "status": "DONE",
    "created_at": "...",
    "completed_at": null
  }
}
```

Success returns HTTP 200. Business failures, such as a missing item or no free shelf, return HTTP 409.

### POST `/api/v1/orders/retrieve`

Request body:

```json
{
  "item_id": 1
}
```

The route requires an integer `item_id`, logs validation failures, and calls `retrieve_item()`. A successful retrieval returns HTTP 200; a missing item or an item not currently on a shelf returns HTTP 409.

### GET `/api/v1/events`

The route orders events by descending timestamp and returns at most the newest 50 events.

## 7. Store flow in exact execution order

Starting with `POST /api/v1/orders/store`:

1. Flask matches `/api/v1/orders/store` to `store_item_route()`.
2. JSON is read with `request.get_json(silent=True)`. Missing or invalid JSON becomes `{}`.
3. The route validates the four request fields.
4. On validation failure, `log_event()` inserts a failure event and the route returns 400.
5. On valid input, `store_item()` queries the item by primary key.
6. If the item does not exist, it returns failure immediately. No order is created in this branch.
7. Otherwise, it creates an order with action `STORE` and status `PENDING`, then commits it.
8. `_height_to_class()` maps item height to the smallest class that can contain it:
   - height <= 15 -> 15
   - height <= 20 -> 20
   - every larger height -> 32
9. `find_shelf()` searches for a free shelf.
10. If no shelf is found, the existing order becomes `FAILED`, a failure event is appended, and HTTP 409 is returned.
11. If a shelf is found, the shelf becomes occupied, its `item_id` is set, the item status becomes `STORED`, and the order receives `assigned_shelf_id` and status `DONE`.
12. Those state changes are committed.
13. A successful `STORE` event is appended and committed.
14. The route serializes the order and returns the result.

## 8. Placement algorithm

`find_shelf(target_x, target_y, target_layer, height_class)` uses this order:

1. Query the exact requested coordinates and layer for any unoccupied shelf. This first query does not check the shelf's `height_class`.
2. If the exact position is unavailable, search the requested layer for the nearest free shelf with the required height class.
3. If that fails, search the other layer for the same height class.
4. If that fails, search both layers for progressively taller classes.
5. Return `None` when no candidate exists.

Nearest means Manhattan distance:

```text
distance = abs(target_x - shelf.x) + abs(target_y - shelf.y)
```

The implementation uses Python's `min()` over database results. Equal-distance candidates are resolved by query result order, not by an explicit tie-breaker.

## 9. Retrieve flow in exact execution order

Starting with `POST /api/v1/orders/retrieve`:

1. Flask matches the route and validates that `item_id` is an integer.
2. Invalid input is logged as `VALIDATION_ERROR` and returns 400.
3. `retrieve_item()` queries the item.
4. If the item does not exist, it returns failure without creating an order.
5. It searches for an occupied shelf whose `item_id` matches.
6. It creates a `RETRIEVE` order with status `PENDING` and commits it.
7. If no matching shelf exists, the order becomes `FAILED`, a failure event is appended, and the route returns 409.
8. Otherwise, the shelf is freed and its `item_id` cleared.
9. The item status becomes `RETRIEVED`.
10. The order receives the shelf ID and becomes `DONE`.
11. The state changes are committed.
12. A successful `RETRIEVE` event is appended and committed.
13. The route returns the serialized order and success message.

## 10. Event logging flow

`log_event()` constructs an `Event`, adds it to the current SQLAlchemy session, and commits immediately. The current call sites log:

- invalid store or retrieve input as `VALIDATION_ERROR` / `FAILURE`
- failed store due to no shelf as `STORE` / `FAILURE`
- successful store as `STORE` / `SUCCESS`
- failed retrieve as `RETRIEVE` / `FAILURE`
- successful retrieve as `RETRIEVE` / `SUCCESS`

The documented `PLACEMENT_FAILED` action is not currently emitted by the code.

## 11. Physical machine integration

`app/logic/machine_interface.py` wraps the synchronous `asyncua` client. It defines paths for documented OPC UA nodes such as `Einlagern`, `Auslagern`, emergency stop, collision status, and control enabled.

The intended sequence is:

1. Construct `MachineInterface`.
2. Connect to the configured endpoint.
3. Check `is_control_enabled()` and `is_safe()`.
4. Call `trigger_store()` or `trigger_retrieve()`.
5. Disconnect.

This is not part of the current API flow. `ENDPOINT_URL` still contains a placeholder PLC address, and the module is not imported by `order_manager.py`. The physical machine therefore does not move when the current store or retrieve endpoints are called.

## 12. What is not implemented yet

These items appear in the roadmap or imports but are absent from the current runtime:

- dashboard route and dashboard HTML
- frontend JavaScript and occupancy visualization
- login and user model despite Flask-Login initialization
- authentication protection with `@login_required`
- OPC UA calls from order processing
- machine target-coordinate node discovery and confirmation
- database migrations; `flask-migrate` is listed but not configured
- request schemas despite `marshmallow` being listed
- explicit transaction rollback across the whole store/retrieve process
- `completed_at` updates
- `target_shelf_id` assignment
- addressability flags
- automated tests

## 13. Important implementation notes

### Transaction behavior differs from the docstring

`order_manager.py` says the complete operation rolls back if a later step fails. In the current code, the order is committed before placement, the main state is committed before event logging, and `log_event()` commits separately. There is no `try/except` with `db.session.rollback()`, so the implementation does not provide one atomic transaction across order, shelf, item, and event changes.

### Height validation is incomplete

`_height_to_class()` maps every height above 20 cm to 32 cm, including values above 32 cm and negative values. The item endpoint also accepts values without checking their type or range.

### Exact shelf selection does not check capacity

If the requested coordinates are free, the first placement query returns that shelf even when its `height_class` is smaller than the item's required class. Capacity is only checked during fallback searches.

### Database creation is not migration

`db.create_all()` creates missing tables but does not safely apply schema changes to an existing database. Changing a model later requires a migration strategy or a controlled database rebuild.

### Security defaults are for development only

The secret key is hard-coded, debug mode is enabled by `run.py`, and no authentication route exists. These settings should not be used for a production warehouse deployment.

## 14. Suggested manual test sequence

From the `WMS` directory:

```powershell
pip install -r requirements.txt
python run.py
```

In another terminal, seed shelves once:

```powershell
python seed_shelves.py
```

Then use the following requests in order:

1. `GET http://127.0.0.1:5000/api/v1/shelves` and confirm shelf rows exist.
2. `POST http://127.0.0.1:5000/api/v1/items` with the example item body.
3. `POST http://127.0.0.1:5000/api/v1/orders/store` using the returned item ID.
4. `GET http://127.0.0.1:5000/api/v1/shelves` and confirm one shelf is occupied.
5. `GET http://127.0.0.1:5000/api/v1/events` and confirm the store event.
6. `POST http://127.0.0.1:5000/api/v1/orders/retrieve` with the same item ID.
7. Query shelves and events again to confirm the shelf is free and retrieval was logged.

## 15. One-page mental model

```text
Register item
    |
    v
POST /api/v1/orders/store
    |
    +--> validate request ---- invalid --> VALIDATION_ERROR event, 400
    |
    +--> find item ----------- missing --> 409
    |
    +--> create PENDING order
    |
    +--> convert item height to class
    |
    +--> find free shelf
    |       |
    |       +--> none --> FAILED order + failure event, 409
    |       |
    |       +--> found --> occupy shelf, mark item STORED,
    |                      mark order DONE, success event, 200
    |
    v
POST /api/v1/orders/retrieve
    |
    +--> validate and find item
    +--> create PENDING order
    +--> find occupied shelf for item
    +--> free shelf and mark item RETRIEVED
    +--> mark order DONE and append event
```
