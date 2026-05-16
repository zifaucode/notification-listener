#!/data/data/com.termux/files/usr/bin/bash
# ================================================================
# start.sh — Script startup NOTIFICATION-LISTENER
# Jalankan dengan: bash scripts/start.sh
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

PID_FILE="$PROJECT_ROOT/server.pid"
LOG_FILE="$PROJECT_ROOT/server.log"
TUNNEL_LOG="$PROJECT_ROOT/tunnel.log"
CF_PID_FILE="$PROJECT_ROOT/cloudflared.pid"

# Warna
G="\e[32m"
Y="\e[33m"
C="\e[36m"
R="\e[31m"
W="\e[0m"
B="\e[1m"

clear
echo -e "${C}${B}"
echo "╔══════════════════════════════════════════════════╗"
echo "║     NOTIFICATION-LISTENER - by ZIFAUCODE         ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${W}"

# ─── Step 1: Bersihkan proses lama ──────────────────────────────
echo -e " ${G}[1/3]${W} Mematikan proses lama jika ada..."
pkill -f "python run.py" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 1

# ─── Step 2: Jalankan Python server ────────────────────────────
echo -e " ${G}[2/3]${W} Memulai Python server di background..."

# PENTING: Gunakan --no-tunnel agar Python TIDAK menjalankan cloudflared sendiri.
# Cloudflared akan dijalankan dari script ini saja (step 3).
nohup python run.py --no-tunnel > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"
echo -e "        ✅ Server berjalan (PID: $SERVER_PID)"

# Tunggu server siap
sleep 2

# ─── Step 3: Jalankan Cloudflare Tunnel ────────────────────────
echo -e " ${G}[3/3]${W} Memulai Cloudflare Quick Tunnel..."

CLOUDFLARED_LOG="$TUNNEL_LOG"

# Gunakan SSL_CERT_FILE dari Termux agar Cloudflared bisa memverifikasi sertifikat TLS
nohup env SSL_CERT_FILE="$PREFIX/etc/tls/cert.pem" \
    termux-chroot cloudflared tunnel --url http://localhost:5000 \
    --no-autoupdate \
    > "$CLOUDFLARED_LOG" 2>&1 &
CF_PID=$!
echo $CF_PID > "$CF_PID_FILE"

echo -e "        ⏳ Menunggu Cloudflare URL..."

# Tunggu URL muncul di log (max 30 detik)
PUBLIC_URL=""
for i in $(seq 1 30); do
    PUBLIC_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' "$CLOUDFLARED_LOG" 2>/dev/null \
        | grep -v 'api.trycloudflare.com' \
        | head -1)
    if [ -n "$PUBLIC_URL" ]; then
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

# ─── Tampilkan Info ────────────────────────────────────────────
echo ""
if [ -n "$PUBLIC_URL" ]; then
    echo -e "${C}╔══════════════════════════════════════════════════════════════╗"
    echo -e "║  ${G}✅ NOTIFICATION-LISTENER SIAP!${C}                               ║"
    echo -e "╠══════════════════════════════════════════════════════════════╣"
    echo -e "║  🌐 ${B}URL Publik${W}  : ${Y}${PUBLIC_URL}${C}"
    echo -e "║  📡 ${B}URL Lokal${W}   : ${Y}http://localhost:5000${C}                      ║"
    echo -e "╠══════════════════════════════════════════════════════════════╣"
    echo -e "║  PID Server     : $SERVER_PID                              ║"
    echo -e "║  PID Cloudflare : $CF_PID                                  ║"
    echo -e "╚══════════════════════════════════════════════════════════════╝${W}"
else
    echo -e " ${R}⚠️  URL Cloudflare belum terdeteksi. Cek log:${W}"
    echo -e "    cat $CLOUDFLARED_LOG"
fi

echo ""
echo -e " Untuk stop semua : ${Y}bash scripts/stop.sh${W}"
echo -e " Untuk lihat log  : ${Y}tail -f $LOG_FILE${W}"
echo ""
