# Warehouse Management System (WMS)

A backend system that manages a high-bay warehouse (Hochregallager) — deciding where items get stored, tracking every shelf's status, and keeping a permanent record of every action. Built as a 10-credit Bachelor's project (BCS Computer Science), tied to the Digitale Fabrik / Industry 4.0 concept, with a designed (not yet connected) integration path to the real physical warehouse machine via OPC UA.

## What this project does

- Registers items and decides which shelf to place them on
- Automatically finds the nearest free shelf if the requested one is occupied
- Tracks every shelf, item, order, and event in a database
- Exposes a REST API so external tools (or eventually the real machine) can interact with it
- Is designed to connect to the lab's real Siemens PLC via OPC UA, once network details are available

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.14 |
| Web framework | Flask |
| Database | SQLite (via Flask-SQLAlchemy) |
| Machine interface | OPC UA (via `asyncua`) |
| Config | `.env` file (via `python-dotenv`) |

## Project structure

```
WMS/
├── app/
│   ├── __init__.py          # Creates and configures the Flask app
│   ├── api/
│   │   └── routes.py        # REST API endpoints (/shelves, /items, /orders/...)
│   ├── models/               # Database tables
│   │   ├── shelves.py
│   │   ├── items.py
│   │   ├── orders.py
│   │   └── events.py
│   └── logic/                 # Business logic
│       ├── placement_engine.py   # Decides which shelf to use
│       ├── order_manager.py      # Runs the full store/retrieve process
│       ├── event_logger.py       # Permanent audit log
│       └── machine_interface.py  # Real machine connection (OPC UA)
├── static/                    # Dashboard front-end assets (planned)
├── templates/                  # Dashboard HTML (planned)
├── instance/                    # SQLite database file lives here (not committed)
├── main.py                       # Application entry point
├── seed_shelves.py                # One-time script to fill the database with shelf positions
├── requirements.txt
├── .env.example                    # Template for your own .env file
└── .gitignore
```

## Architecture

```
Operator  →  API / Dashboard  →  Business Logic  →  SQLite Database  →  OPC UA (Siemens PLC)  →  Physical Warehouse
```

Six layers, each only talking to the layer directly above or below it — so, for example, swapping SQLite for PostgreSQL later would only require changing the database layer, nothing else.

## Setup — run this once

```bash
# 1. Clone the repository
git clone https://github.com/ishitadudhal/WarehouseManagement.git
cd WarehouseManagement/WMS

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
# source venv/bin/activate       # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your environment file
copy .env.example .env           # Windows
# cp .env.example .env           # macOS/Linux
# then edit .env with your own values if needed

# 5. Create the database and fill it with shelf positions
python seed_shelves.py
```

## Running the app

```bash
python main.py
```

The server starts at `http://127.0.0.1:5000`.

## API Endpoints

| Method | Endpoint | What it does |
|---|---|---|
| GET | `/api/v1/shelves` | List all shelf positions and their status |
| GET | `/api/v1/items` | List all registered items |
| POST | `/api/v1/items` | Register a new item |
| POST | `/api/v1/orders/store` | Store an item on a shelf |
| POST | `/api/v1/orders/retrieve` | Retrieve an item from its shelf |
| GET | `/api/v1/events` | View the last 50 logged events |

### Example — register an item

```bash
curl -X POST http://127.0.0.1:5000/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Box A","height":18,"width":20,"depth":20,"weight":3.5}'
```

### Example — store it

```bash
curl -X POST http://127.0.0.1:5000/api/v1/orders/store \
  -H "Content-Type: application/json" \
  -d '{"item_id":1,"target_x":3,"target_y":4,"target_layer":1}'
```

## Database

Four tables, matching the physical warehouse (2 layers, 7 rows, 8 columns → 112 shelf positions):

- **shelves** — position, height class, whether occupied, which item is on it
- **items** — name, dimensions, current status
- **orders** — every store/retrieve request, what was requested vs what actually happened
- **events** — permanent, append-only log of every action taken

## Real machine integration (in progress)

The physical warehouse in the lab is controlled by a Siemens PLC exposing an OPC UA server (documented in Y. Ubben's 2025 master's thesis, Hochschule Emden/Leer). `app/logic/machine_interface.py` is written against that real, documented node structure (`Einlagern`, `Auslagern`, safety checks) but is not yet connected — it needs the server's real IP address, to be set in `.env` as `OPCUA_ENDPOINT_URL`.

## Status

- [x] Database design and models
- [x] Placement Engine, Order Manager, Event Logger
- [x] REST API, tested end-to-end (store + retrieve)
- [x] Machine interface module written against real documented protocol
- [ ] Operator Dashboard (web UI)
- [ ] Live connection to the physical machine
- [ ] Automated tests

## Author

Ishita Dudhal — BCS Computer Science
