"""
Notification Listener Service — App Factory.

Inisialisasi FastAPI app, middleware, mount static files,
dan jalankan background services saat startup.
"""

import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR, PORT
from app import database as db
from app import worker
from app import tunnel

START_TIME = time.time()
_app_instance = None


def create_app() -> FastAPI:
    """Factory untuk membuat instance FastAPI."""

    application = FastAPI(
        title="Notification Listener Service",
        version="2.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None
    )

    # ── CORS ────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Static Files ────────────────────────────────────────────
    application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # ── Startup Event ───────────────────────────────────────────
    @application.on_event("startup")
    def on_startup():
        db.init_db()
        worker.start_listener()

        # Jika dijalankan dari start.sh dengan --no-tunnel,
        # cloudflared dikelola oleh shell script, bukan Python.
        no_tunnel = os.getenv("NO_TUNNEL", "0") == "1"
        if no_tunnel:
            print(f"[App] ℹ️  Mode --no-tunnel: Cloudflared dikelola oleh shell script")
        else:
            tunnel.start_tunnel(port=PORT)

        print(f"[App] ✅ Notification Listener Service berjalan di port {PORT}")

    # ── Import & include routes ─────────────────────────────────
    from app.main import router
    application.include_router(router)

    global _app_instance
    _app_instance = application

    return application
