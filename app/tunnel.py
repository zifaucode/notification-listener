"""
Tunnel — Mengelola Cloudflare Quick Tunnel (cloudflared).

FIX: Tunnel sekarang berjalan persisten setelah URL ditemukan.
Sebelumnya, loop break setelah menemukan URL → tunnel langsung di-terminate.
"""

import subprocess
import re
import threading
import time

from app import database as db

TUNNEL_PATTERN = re.compile(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com")

_tunnel_proc = None
_restart_event = threading.Event()
_lock = threading.Lock()


def _run_tunnel(port=5000):
    """Loop utama tunnel — restart otomatis jika mati."""
    global _tunnel_proc

    while True:
        try:
            db.set_tunnel_info("", "starting")
            print(f"[Tunnel] 🚀 Memulai cloudflared tunnel pada port {port}...")

            with _lock:
                _tunnel_proc = subprocess.Popen(
                    ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

            url = None

            # Baca stdout cloudflared secara terus-menerus
            # INI YANG MEMBUAT TUNNEL TETAP HIDUP — jangan break setelah menemukan URL
            for line in _tunnel_proc.stdout:
                # Jika ada request restart, keluar dari loop
                if _restart_event.is_set():
                    print("[Tunnel] 🔄 Restart diminta, menghentikan tunnel...")
                    break

                # Cari URL tunnel dari output cloudflared
                match = TUNNEL_PATTERN.search(line)
                if match and url is None:
                    url = match.group(0)
                    db.set_tunnel_info(url, "active")
                    print(f"[Tunnel] ✅ Aktif: {url}")
                    # TIDAK break di sini — terus baca stdout agar proses tidak mati

            # Proses cloudflared sudah selesai (mati sendiri atau di-restart)
            with _lock:
                if _tunnel_proc and _tunnel_proc.poll() is None:
                    _tunnel_proc.terminate()
                    try:
                        _tunnel_proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        _tunnel_proc.kill()
                _tunnel_proc = None

            _restart_event.clear()
            db.set_tunnel_info(url or "", "disconnected")
            print("[Tunnel] ⚠️  Tunnel terputus, restart dalam 5 detik...")

        except FileNotFoundError:
            db.set_tunnel_info("", "error: cloudflared not found")
            print("[Tunnel] ❌ cloudflared tidak ditemukan. Jalankan setup_termux.sh")
        except Exception as e:
            db.set_tunnel_info("", f"error: {e}")
            print(f"[Tunnel] ❌ Error: {e}")

        time.sleep(5)


def start_tunnel(port=5000):
    """Jalankan tunnel sebagai daemon thread."""
    t = threading.Thread(target=_run_tunnel, args=(port,), daemon=True, name="CfTunnel")
    t.start()
    return t


def restart_tunnel():
    """Minta tunnel untuk restart."""
    _restart_event.set()
    with _lock:
        if _tunnel_proc and _tunnel_proc.poll() is None:
            _tunnel_proc.terminate()
            print("[Tunnel] 🔄 Sinyal restart dikirim")
