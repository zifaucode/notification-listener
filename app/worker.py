"""
Worker — Background thread yang membaca notifikasi Android via termux-notification-list.

Berjalan sebagai daemon thread, polling setiap 2 detik.
"""

import subprocess
import json
import time
import threading

from app import database as db
from app import webhook as wh


def _get_notifications():
    """Ambil daftar notifikasi aktif dari Termux:API."""
    try:
        result = subprocess.run(
            ["termux-notification-list"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data if isinstance(data, list) else []
    except FileNotFoundError:
        print("[Listener] ⚠️  termux-notification-list tidak ditemukan. Install Termux:API.")
    except subprocess.TimeoutExpired:
        print("[Listener] ⚠️  termux-notification-list timeout.")
    except json.JSONDecodeError:
        print("[Listener] ⚠️  Output termux-notification-list bukan JSON valid.")
    except Exception as e:
        print(f"[Listener] ❌ Error: {e}")
    return []


def _run_listener():
    """Loop utama notification listener."""
    print("[Listener] ✅ Notification listener aktif, polling setiap 2 detik...")
    seen = set()

    while True:
        try:
            notifications = _get_notifications()
            packages = db.get_allowed_packages()

            for n in notifications:
                pkg = n.get("packageName", "") or n.get("pkg", "")
                notif_id = str(n.get("id", ""))
                text = " ".join(filter(None, [
                    n.get("title", ""),
                    n.get("content", ""),
                    n.get("text", "")
                ]))
                key = f"{pkg}:{notif_id}:{text[:80]}"

                if pkg in packages and key not in seen:
                    seen.add(key)
                    amount = wh.parse_amount(text)
                    db.add_notification_log(pkg, text, amount)
                    wh.send_webhook(pkg, text, amount)
                    print(f"[Listener] 📩 Notifikasi baru: {pkg} => Rp{amount:,}")

            # Bersihkan seen set jika terlalu besar untuk mencegah memory leak
            if len(seen) > 10000:
                seen.clear()
                print("[Listener] 🔄 Cache notifikasi di-reset (>10.000 entri)")

        except Exception as e:
            print(f"[Listener] ❌ Error di loop utama: {e}")

        time.sleep(2)


def start_listener():
    """Jalankan notification listener sebagai daemon thread."""
    t = threading.Thread(target=_run_listener, daemon=True, name="NotifListener")
    t.start()
    return t
