"""
Routes — Semua endpoint HTTP untuk Notification Listener Service.
"""

import os
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from app.config import STATIC_DIR
from app import database as db
from app import auth
from app import webhook as wh
from app import tunnel

router = APIRouter()


def _serve_html(filename: str) -> HTMLResponse:
    """Helper: baca dan sajikan file HTML dari static/."""
    path = os.path.join(str(STATIC_DIR), filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content=f"<h1>{filename} tidak ditemukan</h1>", status_code=404)


# ── Pages ───────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def root():
    """Halaman utama: redirect ke setup atau login."""
    settings = db.get_settings()
    target = "setup.html" if (not settings or not settings.get("is_initialized")) else "login.html"
    return _serve_html(target)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    """Halaman dashboard monitoring."""
    return _serve_html("dashboard.html")


@router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
def swagger_docs():
    """Swagger UI docs (wajib login via localStorage token)."""
    return _serve_html("docs.html")


# ── Auth ────────────────────────────────────────────────────────

@router.post("/setup")
def setup(req: dict):
    """Initial setup — hanya bisa dijalankan sekali."""
    settings = db.get_settings()
    if settings and settings.get("is_initialized"):
        raise HTTPException(403, "Setup sudah dilakukan. Endpoint dinonaktifkan.")

    username = req.get("username")
    password = req.get("password")
    api_key = req.get("api_key")
    webhook_url = req.get("webhook_url")

    if not all([username, password, api_key, webhook_url]):
        raise HTTPException(400, "Semua field wajib diisi")

    db.create_settings(username, auth.hash_password(password), api_key, webhook_url)
    return {"success": True}


@router.post("/login")
def login(req: dict):
    """Login dashboard — mengembalikan JWT token."""
    settings = db.get_settings()
    if not settings:
        raise HTTPException(400, "Belum diinisialisasi")

    if auth.verify_password(req.get("password", ""), settings.get("password_hash", "")):
        return {"token": auth.create_token(settings["username"])}
    raise HTTPException(401, "Password salah")


# ── API: Status & Stats ────────────────────────────────────────

@router.get("/api/status")
def get_status(user: str = Depends(auth.verify_token)):
    """Status server & uptime."""
    from app import START_TIME
    uptime = int(time.time() - START_TIME)
    return {"status": "running", "uptime_seconds": uptime}


@router.get("/api/stats")
def get_stats(user: str = Depends(auth.verify_token)):
    """Statistik ringkasan (notif count, webhook success/failed)."""
    return db.get_stats()


# ── API: Configuration ─────────────────────────────────────────

@router.get("/api/config")
def get_config(user: str = Depends(auth.verify_token)):
    """Lihat konfigurasi saat ini."""
    settings = db.get_settings()
    return {
        "webhook_url": settings.get("webhook_url") if settings else "",
        "api_key": settings.get("api_key") if settings else "",
        "packages": db.get_allowed_packages()
    }


@router.post("/api/config")
def update_config(req: dict, user: str = Depends(auth.verify_token)):
    """Update webhook URL dan/atau API key."""
    db.update_settings(api_key=req.get("api_key"), webhook_url=req.get("webhook_url"))
    return {"success": True}


# ── API: Package Management ────────────────────────────────────

@router.post("/api/packages")
def add_package(req: dict, user: str = Depends(auth.verify_token)):
    """Tambah package name ke whitelist."""
    pkg = req.get("package_name")
    if not pkg:
        raise HTTPException(400, "package_name wajib diisi")
    db.add_allowed_package(pkg)
    return {"success": True}


@router.delete("/api/packages/{package_name}")
def delete_package(package_name: str, user: str = Depends(auth.verify_token)):
    """Hapus package dari whitelist."""
    db.remove_allowed_package(package_name)
    return {"success": True}


# ── API: Logs ───────────────────────────────────────────────────

@router.get("/api/logs/notifications")
def get_notif_logs(user: str = Depends(auth.verify_token)):
    """Log notifikasi masuk."""
    return db.get_notification_logs()


@router.get("/api/logs/webhooks")
def get_webhook_logs(user: str = Depends(auth.verify_token)):
    """Log pengiriman webhook."""
    return db.get_webhook_logs()


# ── API: Tunnel ─────────────────────────────────────────────────

@router.get("/api/tunnel")
def get_tunnel(user: str = Depends(auth.verify_token)):
    """Info tunnel Cloudflare (URL & status)."""
    return db.get_tunnel_info()


# ── API: Control ────────────────────────────────────────────────

@router.post("/api/restart/tunnel")
def restart_tunnel_api(user: str = Depends(auth.verify_token)):
    """Restart Cloudflare tunnel."""
    tunnel.restart_tunnel()
    return {"success": True, "message": "Tunnel sedang di-restart"}


@router.post("/api/restart/service")
def restart_service_api(user: str = Depends(auth.verify_token)):
    """Info restart service (manual via stop & start)."""
    return {"success": True, "message": "Restart manual: hentikan dan jalankan ulang aplikasi"}


# ── API: Testing (Protected) ───────────────────────────────────

@router.post("/test/notification")
def test_notification(req: dict, user: str = Depends(auth.verify_token)):
    """Test kirim notifikasi manual (dilindungi auth)."""
    pkg = req.get("package", "com.test.app")
    text = req.get("text", "")
    amount = wh.parse_amount(text)
    db.add_notification_log(pkg, text, amount)
    success = wh.send_webhook(pkg, text, amount)
    return {"amount": amount, "sent": success}


# ── API: OpenAPI Spec ───────────────────────────────────────────

@router.get("/api/openapi.json", include_in_schema=False)
def openapi_json(user: str = Depends(auth.verify_token)):
    """OpenAPI spec JSON (protected)."""
    from app import create_app
    # Return spec dari app yang sudah ada
    from fastapi import Request
    # Workaround: akses app melalui modul
    import app as app_module
    return app_module._app_instance.openapi() if hasattr(app_module, '_app_instance') else {}
