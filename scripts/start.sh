#!/data/data/com.termux/files/usr/bin/bash

# Warna
G="\e[32m"
Y="\e[33m"
C="\e[36m"
W="\e[0m"
B="\e[1m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

PID_FILE="$PROJECT_ROOT/server.pid"
LOG_FILE="$PROJECT_ROOT/server.log"

clear
echo -e "${C}${B}"
echo "╔══════════════════════════════════════════════════╗"
echo "║     NOTIFICATION-LISTENER - by ZIFAUCODE         ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${W}"

if [ -f "$PID_FILE" ]; then
    SERVER_PID=$(cat "$PID_FILE")
    if kill -0 "$SERVER_PID" 2>/dev/null; then
        echo -e " ${Y}⚠️  Service sudah berjalan dengan PID: ${SERVER_PID}${W}"
        echo -e " ${Y}   Dashboard: http://localhost:5000${W}"
        echo ""
        exit 0
    fi
fi

echo -e " ${G}[*]${W} Mengaktifkan Wake-Lock..."
termux-wake-lock

echo -e " ${G}[*]${W} Memulai service di background..."
nohup python run.py > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"
sleep 1

echo -e "${C}"
echo "┌──────────────────────────────────────────────────┐"
echo -e "│  ${B}STATUS${W}      : ${G}BERJALAN DI BACKGROUND${C}            │"
echo -e "│  ${B}PID${W}         : ${SERVER_PID,-31}${C} │"
echo -e "│  ${B}WAKE-LOCK${W}   : ${G}AKTIF${W} (Mencegah Android sleep)      ${C}│"
echo -e "│  ${B}LOG FILE${W}    : ${LOG_FILE,-31}${C} │"
echo "│                                                  │"
echo -e "│  🌐 ${B}DASHBOARD${W}: ${Y}http://localhost:5000${C}             │"
echo "└──────────────────────────────────────────────────┘"
echo -e "${W}"
echo " Tip: Gunakan perintah 'bash scripts/stop.sh' untuk menghentikan bot."
echo ""
