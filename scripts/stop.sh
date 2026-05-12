#!/data/data/com.termux/files/usr/bin/bash

# Warna
G="\e[32m"
Y="\e[33m"
C="\e[36m"
R="\e[31m"
W="\e[0m"
B="\e[1m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

PID_FILE="$PROJECT_ROOT/server.pid"

clear
echo -e "${C}${B}"
echo "╔══════════════════════════════════════════════════╗"
echo "║     NOTIFICATION-LISTENER - by ZIFAUCODE         ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${W}"
echo -e " ${Y}[*]${W} Memulai proses penghentian bot..."

if [ -f "$PID_FILE" ]; then
    SERVER_PID=$(cat "$PID_FILE")
    if kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID"
        echo -e " ${G}[✔]${W} Server (PID ${C}$SERVER_PID${W}) berhasil dihentikan."
    else
        echo -e " ${Y}[!]${W} PID $SERVER_PID tidak berjalan, membersihkan file PID."
    fi
    rm -f "$PID_FILE"
else
    echo -e " ${Y}[!]${W} File PID tidak ditemukan. Menghentikan semua proses 'python run.py'..."
    pkill -f "python run.py" || true
    echo -e " ${G}[✔]${W} Proses Python dibersihkan."
fi

# Matikan cloudflared jika masih ada yang nyangkut
pkill -f "cloudflared tunnel" || true
echo -e " ${G}[✔]${W} Cloudflared tunnel process dihentikan (jika ada)."

# Lepaskan wakelock agar baterai normal
termux-wake-unlock
echo -e " ${G}[✔]${W} Wake-Lock dilepaskan (Android bisa sleep normal)."

echo ""
echo -e "${C}"
echo "┌──────────────────────────────────────────────────┐"
echo -e "│  ${B}STATUS${W}      : ${R}BOT BERHASIL DIHENTIKAN${C}             │"
echo "└──────────────────────────────────────────────────┘"
echo -e "${W}"

