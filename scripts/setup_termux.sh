#!/data/data/com.termux/files/usr/bin/bash
# ================================================================
# setup_termux.sh — One-time setup BOT-ANDRO di Termux
#
# Cara penggunaan:
#   1. Install Termux dari F-Droid (BUKAN dari Play Store)
#   2. Copy folder NOTIFICATION-LISTENER ke HP
#   3. Di Termux jalankan:
#        bash scripts/setup_termux.sh
# ================================================================

set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     NOTIFICATION-LISTENER — Setup Termux             ║"
echo "╚══════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ─── Termux User Repository (TUR) Index ─────────────────────────
TUR_INDEX="https://termux-user-repository.github.io/pypi/"

# ─── 0. Mencegah Android Sleep ──────────────────────────────────
echo "[0/7] Mengaktifkan Termux Wake-Lock (Agar jalan di background)..."
termux-wake-lock

# ─── 1. Update package list ─────────────────────────────────────
echo "[1/7] Update & upgrade packages Termux..."
pkg update -y && pkg upgrade -y

# ─── 2. Install dependencies system ─────────────────────────────
echo ""
echo "[2/7] Install dependencies sistem Android (Python, Git, ADB, dll)..."
pkg install -y \
    python \
    termux-api \
    git \
    wget \
    clang \
    make \
    binutils \
    libffi \
    openssl \
    rust

# ─── 3. Upgrade pip & setuptools ────────────────────────────────
echo ""
echo "[3/7] Menyiapkan pip & build tools..."
python -m ensurepip --upgrade 2>/dev/null || true
pip install --upgrade pip setuptools wheel 2>/dev/null || true

# ─── 4. Install Python dependencies ─────────────────────────────
echo ""
echo "[4/7] Install library dependencies Python..."

echo "    > [1/3] Menginstall pydantic-core & bcrypt dari Termux User Repository..."
echo "    ⏳ Menggunakan pre-built wheel dari TUR (lebih cepat & stabil)..."
pip install --extra-index-url "$TUR_INDEX" pydantic-core bcrypt || {
    echo "    ⚠️  TUR gagal untuk beberapa library, mencoba fallback compile dari source..."
    CARGO_BUILD_TARGET="" pip install pydantic-core bcrypt --no-binary :none:
}

echo "    > [2/3] Menginstall dependencies lainnya..."
pip install -r "$PROJECT_ROOT/requirements.txt"

# ─── 5. Verifikasi instalasi Python ─────────────────────────────
echo ""
echo "[5/7] Verifikasi instalasi Python..."

VERIFY_FAILED=0
for pkg_name in fastapi uvicorn requests dotenv bcrypt jwt python_multipart; do
    MOD_NAME="$pkg_name"
    if [ "$pkg_name" = "python_multipart" ]; then
        MOD_NAME="multipart"
    fi
    if python -c "import $MOD_NAME" 2>/dev/null; then
        echo "    ✅ $pkg_name OK"
    else
        echo "    ❌ $pkg_name GAGAL diimport!"
        VERIFY_FAILED=1
    fi
done

if [ "$VERIFY_FAILED" -eq 1 ]; then
    echo ""
    echo "    ⚠️  Beberapa library gagal diinstall. Proses mungkin berlanjut tetapi bisa error."
fi

# ─── 6. Install Cloudflared ─────────────────────────────────────
echo ""
echo "[6/7] Install cloudflared (Cloudflare Quick Tunnel)..."

ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    CF_ARCH="arm64"
elif [ "$ARCH" = "armv7l" ] || [ "$ARCH" = "armv7" ]; then
    CF_ARCH="arm"
else
    echo "    ⚠️  Arsitektur tidak dikenal: $ARCH (coba arm64)"
    CF_ARCH="arm64"
fi

echo "    Arsitektur terdeteksi: $ARCH → cloudflared-linux-$CF_ARCH"

CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$CF_ARCH"
wget -q --show-progress "$CF_URL" -O "$PREFIX/bin/cloudflared"
chmod +x "$PREFIX/bin/cloudflared"

CLOUDFLARED_VERSION=$(cloudflared --version 2>&1 | head -1)
echo "    ✅ $CLOUDFLARED_VERSION"

# ─── 7. Setup konfigurasi & folder ──────────────────────────────
echo ""
echo "[7/7] Membuat file .env & folder yang diperlukan..."

ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
    echo "    ✅ $ENV_FILE dibuat"
else
    echo "    ℹ️  $ENV_FILE sudah ada, tidak ditimpa"
fi

# Beri izin eksekusi ke script
chmod +x "$SCRIPT_DIR/start.sh" "$SCRIPT_DIR/stop.sh" "$SCRIPT_DIR/setup_termux.sh"

# ─── Setup Termux Boot ──────────────────────────────────────────
echo ""
echo "    > Menyiapkan auto-start saat HP reboot (Termux:Boot)..."
mkdir -p ~/.termux/boot
BOOT_SCRIPT=~/.termux/boot/start-listener.sh
cat <<EOF > "$BOOT_SCRIPT"
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
sleep 5
cd "$PROJECT_ROOT"
bash scripts/start.sh
EOF
chmod +x "$BOOT_SCRIPT"
echo "    ✅ Termux:Boot script dibuat"

# ─── Selesai ─────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Setup selesai!                                            ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Langkah selanjutnya:                                         ║"
echo "║                                                               ║"
echo "║  1. PENTING: Aktifkan Akses Notifikasi untuk Termux:API di    ║"
echo "║     pengaturan sistem Android Anda.                           ║"
echo "║                                                               ║"
echo "║  2. Jalankan bot:                                             ║"
echo "║     bash $PROJECT_ROOT/scripts/start.sh                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
