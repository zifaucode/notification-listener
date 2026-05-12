"""
Webhook — Parsing nominal dari teks notifikasi & pengiriman ke Laravel.
"""

import re
import requests
from datetime import datetime

from app import database as db

# Pattern untuk mendeteksi nominal Rupiah dalam berbagai format:
#   Rp10.000  |  Rp 10.000  |  Rp10,000  |  Rp 10.123,00
AMOUNT_PATTERN = re.compile(r"Rp\.?\s?([\d\.,]+)", re.IGNORECASE)


def parse_amount(text: str) -> int:
    """Ekstrak nominal angka dari teks notifikasi.

    Returns:
        int: Nominal dalam rupiah (tanpa desimal). 0 jika tidak ditemukan.
    """
    if not text:
        return 0
    match = AMOUNT_PATTERN.search(text)
    if match:
        raw = match.group(1)
        # Hapus semua separator (titik dan koma)
        # Jika ada koma diikuti tepat 2 digit di akhir, itu desimal → buang
        raw = re.sub(r',(\d{2})$', '', raw)  # Hapus ",00" di akhir
        raw = raw.replace(".", "").replace(",", "")
        try:
            return int(raw)
        except ValueError:
            return 0
    return 0


def send_webhook(package_name: str, raw_text: str, amount: int) -> bool:
    """Kirim data notifikasi ke Laravel webhook endpoint.

    Returns:
        bool: True jika berhasil (HTTP < 400).
    """
    settings = db.get_settings()
    if not settings or not settings.get("webhook_url"):
        return False

    payload = {
        "amount": amount,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "package": package_name,
        "raw_text": raw_text
    }

    headers = {
        "X-API-KEY": settings.get("api_key", ""),
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(
            settings["webhook_url"],
            json=payload,
            headers=headers,
            timeout=10
        )
        status = "success" if resp.status_code < 400 else "failed"
        db.add_webhook_log(payload, status, f"{resp.status_code}: {resp.text[:500]}")
        return status == "success"
    except Exception as e:
        db.add_webhook_log(payload, "failed", str(e))
        return False
