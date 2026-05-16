#!/usr/bin/env python3
"""
Notification Listener Service — Entry Point.

Usage:
    python run.py              # Jalankan dengan tunnel internal
    python run.py --no-tunnel  # Jalankan TANPA tunnel (tunnel dari shell script)
"""

import sys
import uvicorn

# Parse --no-tunnel flag SEBELUM import app (agar flag terbaca saat create_app)
NO_TUNNEL = "--no-tunnel" in sys.argv

from app.config import PORT, LOG_LEVEL

# Set flag di environment agar create_app() bisa membacanya
import os
os.environ["NO_TUNNEL"] = "1" if NO_TUNNEL else "0"

from app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=PORT,
        reload=False,
        log_level=LOG_LEVEL.lower()
    )
