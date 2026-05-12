#!/usr/bin/env python3
"""
Notification Listener Service — Entry Point.

Usage:
    python run.py
"""

import uvicorn
from app import create_app
from app.config import PORT

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
