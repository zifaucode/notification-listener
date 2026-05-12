"""
Database — Operasi SQLite untuk settings, logs, packages, dan tunnel info.

Semua fungsi menggunakan context manager agar koneksi selalu ditutup.
"""

import sqlite3
import json
from datetime import datetime

from app.config import DB_PATH


def _connect():
    """Buat koneksi SQLite dengan row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Buat tabel jika belum ada."""
    with _connect() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK(id=1),
            username TEXT,
            password_hash TEXT,
            api_key TEXT,
            webhook_url TEXT,
            is_initialized INTEGER DEFAULT 0
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS allowed_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_name TEXT UNIQUE
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_name TEXT,
            raw_text TEXT,
            parsed_amount INTEGER,
            timestamp TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS webhook_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT,
            status TEXT,
            response TEXT,
            created_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS tunnel_info (
            id INTEGER PRIMARY KEY CHECK(id=1),
            url TEXT,
            status TEXT,
            last_updated TEXT
        )''')
        conn.commit()


# ── Settings ────────────────────────────────────────────────────

def get_settings():
    """Ambil settings (singleton row id=1)."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM settings WHERE id=1").fetchone()
        return dict(row) if row else None


def create_settings(username, password_hash, api_key, webhook_url):
    """Buat atau replace settings saat initial setup."""
    with _connect() as conn:
        conn.execute('''INSERT OR REPLACE INTO settings
            (id, username, password_hash, api_key, webhook_url, is_initialized)
            VALUES (1, ?, ?, ?, ?, 1)''',
            (username, password_hash, api_key, webhook_url))
        conn.commit()


def update_settings(api_key=None, webhook_url=None):
    """Update sebagian settings (api_key dan/atau webhook_url)."""
    with _connect() as conn:
        if api_key is not None:
            conn.execute("UPDATE settings SET api_key=? WHERE id=1", (api_key,))
        if webhook_url is not None:
            conn.execute("UPDATE settings SET webhook_url=? WHERE id=1", (webhook_url,))
        conn.commit()


# ── Allowed Packages ────────────────────────────────────────────

def add_allowed_package(package_name):
    """Tambah package ke whitelist (ignore jika sudah ada)."""
    with _connect() as conn:
        try:
            conn.execute("INSERT INTO allowed_packages (package_name) VALUES (?)", (package_name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Sudah ada, skip


def remove_allowed_package(package_name):
    """Hapus package dari whitelist."""
    with _connect() as conn:
        conn.execute("DELETE FROM allowed_packages WHERE package_name=?", (package_name,))
        conn.commit()


def get_allowed_packages():
    """Ambil semua package name yang diizinkan."""
    with _connect() as conn:
        rows = conn.execute("SELECT package_name FROM allowed_packages").fetchall()
        return [r["package_name"] for r in rows]


# ── Notification Logs ───────────────────────────────────────────

def add_notification_log(package_name, raw_text, parsed_amount):
    """Catat notifikasi masuk."""
    with _connect() as conn:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute('''INSERT INTO notification_logs
            (package_name, raw_text, parsed_amount, timestamp)
            VALUES (?, ?, ?, ?)''', (package_name, raw_text, parsed_amount, ts))
        conn.commit()


def get_notification_logs(limit=100):
    """Ambil log notifikasi terbaru."""
    with _connect() as conn:
        rows = conn.execute('''SELECT * FROM notification_logs
            ORDER BY id DESC LIMIT ?''', (limit,)).fetchall()
        return [dict(r) for r in rows]


# ── Webhook Logs ────────────────────────────────────────────────

def add_webhook_log(payload, status, response):
    """Catat hasil pengiriman webhook."""
    with _connect() as conn:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute('''INSERT INTO webhook_logs (payload, status, response, created_at)
            VALUES (?, ?, ?, ?)''', (json.dumps(payload), status, response, ts))
        conn.commit()


def get_webhook_logs(limit=100):
    """Ambil log webhook terbaru."""
    with _connect() as conn:
        rows = conn.execute('''SELECT * FROM webhook_logs
            ORDER BY id DESC LIMIT ?''', (limit,)).fetchall()
        return [dict(r) for r in rows]


# ── Tunnel Info ─────────────────────────────────────────────────

def set_tunnel_info(url, status):
    """Update informasi tunnel (singleton row id=1)."""
    with _connect() as conn:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute('''INSERT OR REPLACE INTO tunnel_info (id, url, status, last_updated)
            VALUES (1, ?, ?, ?)''', (url, status, ts))
        conn.commit()


def get_tunnel_info():
    """Ambil informasi tunnel saat ini."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM tunnel_info WHERE id=1").fetchone()
        return dict(row) if row else None


# ── Statistics ──────────────────────────────────────────────────

def get_stats():
    """Ambil ringkasan statistik."""
    with _connect() as conn:
        notif_count = conn.execute(
            "SELECT COUNT(*) as c FROM notification_logs").fetchone()["c"]
        webhook_success = conn.execute(
            "SELECT COUNT(*) as c FROM webhook_logs WHERE status='success'").fetchone()["c"]
        webhook_failed = conn.execute(
            "SELECT COUNT(*) as c FROM webhook_logs WHERE status='failed'").fetchone()["c"]
        return {
            "notifications": notif_count,
            "webhook_success": webhook_success,
            "webhook_failed": webhook_failed
        }
