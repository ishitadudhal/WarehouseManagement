"""
Main entry point for the WMS (Warehouse Management System) backend.

Run this file to start the application:

    python main.py

The server will start at http://127.0.0.1:5000
Configuration (secret key, database URL, debug mode, OPC UA endpoint) is
read from the ".env" file in this same folder — see .env.example for the
list of variables you can set.
"""

import os
from app import create_app
import app.models  # noqa: F401 — must be imported so db.create_all() sees all tables

flask_app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    flask_app.run(debug=debug, port=port)
