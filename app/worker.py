"""
Worker — Background thread yang membaca notifikasi Android via termux-notification-list.

Berjalan sebagai daemon thread, polling setiap 2 detik.
"""

import subprocess
import json
import time
import threading
import os
import signal
import re

from app import database as db
from app import webhook as wh


def _get_notifications():
    """Ambil daftar notifikasi aktif via ADB Dumpsys."""
    packages = db.get_allowed_packages()
    if not packages:
        return []

    try:
        proc = subprocess.run(
            ["adb", "shell", "dumpsys", "notification", "--noredact"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if proc.returncode != 0:
            if "device offline" in proc.stderr or "no devices" in proc.stderr:
                print("[Listener] ⚠️  ADB belum terhubung! Jalankan 'adb connect 127.0.0.1:5555'.")
            else:
                print(f"[Listener] ⚠️  ADB error: {proc.stderr[:100]}")
            return []
            
        output = proc.stdout
        notifications = []
        
        # Split output per NotificationRecord
        records = output.split("NotificationRecord(")
        for record in records[1:]:
            # Cari nama package
            pkg_match = re.search(r'pkg=([^\s]+)', record)
            if not pkg_match:
                continue
                
            pkg = pkg_match.group(1)
            if pkg not in packages:
                continue
                
            # Cari ID notifikasi
            id_match = re.search(r'id=(\d+)', record)
            notif_id = id_match.group(1) if id_match else "0"
            
            # Cari title (Bisa format String (...) atau CharSequence (...))
            title = ""
            title_match = re.search(r'android\.title=[^\(]*\((.*?)\)\n', record)
            if title_match:
                title = title_match.group(1)
                
            # Cari text
            text = ""
            text_match = re.search(r'android\.text=[^\(]*\((.*?)\)\n', record)
            if text_match:
                text = text_match.group(1)
                
            if title or text:
                notifications.append({
                    "packageName": pkg,
                    "id": notif_id,
                    "title": title,
                    "text": text,
                    "content": ""
                })
                
        return notifications
        
    except FileNotFoundError:
        print("[Listener] ❌ Perintah ADB tidak ditemukan. Install dengan: pkg install android-tools")
    except subprocess.TimeoutExpired:
        print("[Listener] ⚠️  ADB dumpsys timeout. Coba cabut-colok USB atau restart adb server.")
    except Exception as e:
        print(f"[Listener] ❌ Error ekstrak notif: {e}")
        
    return []


def _run_listener():
    """Loop utama notification listener."""
    print("[Listener] ✅ Notification listener aktif, polling setiap 5 detik...")
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
            if len(seen) > 1000:
                seen.clear()
                print("[Listener] 🔄 Cache notifikasi di-reset (>1.000 entri)")

        except Exception as e:
            print(f"[Listener] ❌ Error di loop utama: {e}")
            time.sleep(3)  # Tambah sleep tambahan jika error

        time.sleep(5)  # Interval polling 5 detik (mengurangi penggunaan CPU/RAM)


def start_listener():
    """Jalankan notification listener sebagai daemon thread."""
    t = threading.Thread(target=_run_listener, daemon=True, name="NotifListener")
    t.start()
    return t
