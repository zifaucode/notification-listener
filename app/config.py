"""
Centralized configuration — loads .env and exposes settings.

Semua modul lain mengimpor variabel dari sini, BUKAN langsung dari os.getenv().
"""

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# ── Resolve paths ───────────────────────────────────────────────
# BASE_DIR = root proyek (satu level di atas folder app/)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Load .env dari root proyek
_env_path = BASE_DIR / ".env"
load_dotenv(_env_path)

# ── Server ──────────────────────────────────────────────────────
PORT = int(os.getenv("PORT", "5000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ── Database ────────────────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "data.db"))

# ── Authentication ──────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET or JWT_SECRET == "ganti-dengan-secret-key-yang-kuat":
    JWT_SECRET = secrets.token_hex(32)
    print(f"[Config] ⚠️  JWT_SECRET belum diset, menggunakan random key (tidak persisten)")

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = int(os.getenv("JWT_EXPIRY_DAYS", "7"))
