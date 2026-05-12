# Notification Listener Service

Aplikasi pembaca notifikasi Android (Termux) untuk deteksi pembayaran QRIS dan pengiriman webhook ke Laravel.

## Fitur

- **Notification Listener**: Membaca notifikasi dari aplikasi perbankan / e-wallet via `termux-notification-list`
- **Webhook Sender**: Mengirim data hasil parsing ke endpoint Laravel secara real-time
- **Dashboard Monitoring**: UI web untuk monitoring status, log, dan konfigurasi
- **Cloudflare Tunnel**: Akses dashboard dari jarak jauh melalui tunnel otomatis
- **SQLite Database**: Penyimpanan log notifikasi dan status webhook lokal
- **JWT Authentication**: Login dashboard dengan token JWT

## Struktur File Baru (v2.0)

```
notification-listener/
├── app/                     # Package utama aplikasi
│   ├── __init__.py          # App factory & startup
│   ├── config.py            # Centralized config & dotenv
│   ├── main.py              # FastAPI routes
│   ├── auth.py              # JWT & bcrypt
│   ├── database.py          # SQLite operations
│   ├── webhook.py           # Webhook sender & parser
│   ├── worker.py            # Notification listener
│   └── tunnel.py            # Cloudflared manager
├── scripts/                 # Shell scripts
│   ├── setup_termux.sh      # One-time installer untuk Termux
│   ├── start.sh             # Jalankan service di background
│   └── stop.sh              # Hentikan background service
├── static/                  # PWA Frontend assets
├── docs/                    # Dokumentasi (PRD)
├── run.py                   # Entry point aplikasi
├── requirements.txt         # Python dependencies
├── .env.example             # Contoh environment
└── README.md                # Dokumentasi ini
```

## Instalasi (Termux)

> **PENTING**: Aplikasi ini didesain HANYA untuk dijalankan di Termux pada perangkat Android. Gunakan Termux yang diunduh dari **F-Droid**, bukan Google Play Store.

1. Install Termux & Termux:API dari F-Droid
2. Copy seluruh folder `NOTIFICATION-LISTENER` ke internal storage HP Anda.
3. Buka Termux, masuk ke folder tersebut, dan jalankan script setup:

```bash
cd /sdcard/NOTIFICATION-LISTENER  # (sesuaikan path Anda)
bash scripts/setup_termux.sh
```

Script ini akan secara otomatis:
- Menginstal Python, compiler (clang/rust), dan tools dasar
- Membangun environment untuk librari Python yang tidak pre-built (`pydantic-core`, `bcrypt`) menggunakan Termux User Repository (TUR) fallback.
- Mengunduh & mengatur `cloudflared` untuk arsitektur Anda
- Membuat file `.env` dan token `JWT_SECRET`
- Menyiapkan Auto-Start `Termux:Boot`

## Menjalankan Service

### Secara Manual (Foreground)

```bash
python run.py
```

### Sebagai Background Service (Production)

Gunakan `start.sh` agar service berjalan persisten walau Termux di-minimize:

```bash
bash scripts/start.sh
```

Untuk menghentikan:

```bash
bash scripts/stop.sh
```

## Initial Setup & Dashboard

Akses dashboard di `http://localhost:5000` (atau via URL trycloudflare jika tunnel aktif).

Saat pertama kali diakses, Anda akan diminta melakukan **Initial Setup**:
- Username & Password dashboard
- Laravel API Key
- Laravel Webhook URL

Setelah setup selesai, endpoint `/setup` akan **dikunci secara permanen** untuk keamanan.

## PWA (Progressive Web App)

Dashboard dapat diinstal sebagai PWA:
- Buka dashboard di Chrome Android
- Tekan tombol **Menu Chrome** → **Tambahkan ke Layar Utama**
- Aplikasi akan muncul dengan icon di app drawer Anda.

## API Endpoint Tambahan

- **Swagger UI**: `/docs` (Wajib login di dashboard terlebih dahulu)
- **OpenAPI JSON**: `/api/openapi.json`
- **Manual Test Notification**: `/test/notification` (Auth wajib)

## Keamanan

- **JWT Authentication** melindungi seluruh endpoint API (kecuali halaman publik login/setup).
- **Bcrypt** digunakan untuk meng-hash password admin.
- `database.py` menggunakan _Context Managers_ untuk mencegah resource leak.
- Cloudflare Tunnel berjalan persisten dan secara otomatis terhubung kembali bila koneksi sempat terputus.

## Catatan

Pastikan **Termux:API** telah terinstal dan Anda telah memberikan **Akses Notifikasi** ke aplikasi `Termux:API` pada pengaturan privasi/notifikasi sistem Android Anda.
