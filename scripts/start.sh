#!/data/data/com.termux/files/usr/bin/bash

# Warna
G="\e[32m"
Y="\e[33m"
C="\e[36m"
W="\e[0m"
B="\e[1m"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

PID_FILE="$PROJECT_ROOT/server.pid"
LOG_FILE="$PROJECT_ROOT/server.log"
TUNNEL_LOG="$PROJECT_ROOT/tunnel.log"
CF_PID_FILE="$PROJECT_ROOT/cloudflared.pid"

clear
echo -e "${C}${B}"
echo "╔══════════════════════════════════════════════════╗"
echo "║     NOTIFICATION-LISTENER - by ZIFAUCODE         ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${W}"

echo -e " ${G}[*]${W} Mematikan proses lama jika ada..."
pkill -f "python run.py" 2>/dev/null || true
sleep 1

echo -e " ${G}[*]${W} Memulai Python server di background..."
nohup python run.py > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"
sleep 2

echo -e " ${G}[*]${W} Memulai Cloudflare Quick Tunnel..."

# Matikan tunnel lama jika ada
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 1

# Jalankan cloudflared dengan SSL cert Termux (wajib agar TLS bisa terverifikasi)
nohup env SSL_CERT_FILE="$PREFIX/etc/tls/cert.pem" \
    termux-chroot cloudflared tunnel --url http://localhost:5000 \
    --no-autoupdate \
    > "$TUNNEL_LOG" 2>&1 &
CF_PID=$!
echo $CF_PID > "$CF_PID_FILE"

echo -e " ${G}[*]${W} Menunggu URL tunnel (maks 30 detik)..."

# Poll log hingga URL muncul (max 30 detik)
PUBLIC_URL=""
for i in $(seq 1 30); do
    PUBLIC_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null \
        | grep -v 'api.trycloudflare.com' \
        | head -1)
    if [ -n "$PUBLIC_URL" ]; then
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

echo -e "${C}"
echo "┌──────────────────────────────────────────────────┐"
echo -e "│  ${B}STATUS${W}      : ${G}BERJALAN DI BACKGROUND${C}            │"
printf "│  ${B}PID${W}         : %-31s${C} │\n" "$SERVER_PID"
echo -e "│  ${B}WAKE-LOCK${W}   : ${G}AKTIF${W} (Mencegah Android sleep)      ${C}│"
echo "│                                                  │"
echo -e "│  🌐 ${B}LOKAL${W}    : ${Y}http://localhost:5000${C}             │"
printf "│  🔗 ${B}PUBLIK${W}   : ${Y}%-31s${C} │\n" "${PUBLIC_URL:-Gagal (cek: cat tunnel.log)}"
echo "└──────────────────────────────────────────────────┘"
echo -e "${W}"
echo " Tip: Gunakan perintah 'bash scripts/stop.sh' untuk menghentikan."
echo ""
