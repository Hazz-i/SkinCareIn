# 🌿 SkinSight - AI-Powered Skincare & Dermatological Intelligence API

Backend layanan analisis tipe kulit berbasis deep learning (ResNet-50), deteksi keamanan komposisi bahan skincare via **LiteLLM**, caching artikel berita & edukasi dermatologi di **PostgreSQL**, serta dilengkapi sistem autentikasi **JWT RBAC** dan **Nginx Load Balancer**.

---

## 🚀 Fitur Utama

- **Otentikasi & RBAC (Role-Based Access Control):**
  - Registrasi & login pengguna (`user` & `admin`) dengan hashing password bcrypt dan token JWT.
  - Akses endpoint manajemen khusus admin (seperti trigger scraping manual).
- **Skincare Intelligence via LiteLLM:**
  - Ekstraksi komposisi bahan dari foto kemasan dan analisis kecocokan tipe kulit.
  - Dukungan fallback model multi-provider LLM (Gemini 2.5 Flash -> Gemini 1.5 Flash).
- **Klasifikasi Tipe Kulit (ResNet-50):**
  - Prediksi tipe kulit wajah (kering, normal, berminyak) dari unggahan gambar.
- **Rekomendasi Produk Personal:**
  - Rekomendasi katalog produk berdasarkan tipe kulit pengguna.
- **Caching Dua Tingkat (PostgreSQL):**
  - Daftar berita & edukasi di-cache dalam DB dan disinkronisasi harian (24 jam) via APScheduler.
  - Detail artikel di-scrape 1x saat pertama kali diakses (*Lazy On-Demand Caching*).
- **Performa & Ketahanan:**
  - SlowAPI Rate Limiter untuk proteksi request abuse.
  - Nginx Reverse Proxy & Load Balancer port `8888` mendistribusikan beban ke beberapa instance worker.

---

## 🛠️ Persyaratan Sistem

- Python 3.10+
- PostgreSQL 16+
- Docker & Docker Compose (opsional, untuk menjalankan cluster container)

---

## ⚙️ Konfigurasi Environment (`.env`)

Salin template konfigurasi:
```bash
cp .env.example .env
```

Sesuaikan variabel di dalam `.env`:
```env
# Database
DATABASE_URL=postgresql://postgres:postgrespassword@localhost:5432/skinsight_db

# JWT & Security
JWT_SECRET=your_super_secret_jwt_key_here_minimum_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Akun Admin Default (Auto-seeded)
ADMIN_EMAIL=admin@skinsight.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin123!

# LLM & AI
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini/gemini-2.5-flash
LLM_FALLBACKS=gemini/gemini-1.5-flash
```

---

## 🏃 Menjalankan Aplikasi

### Opsi 1: Menjalankan dengan Docker Compose (Rekomendasi)
Menjalankan PostgreSQL, 2 instance worker API (`api1`, `api2`), dan Nginx load balancer di port `8888`:

```bash
docker compose up --build -d
```

### Opsi 2: Menjalankan Secara Lokal
1. Instal dependensi dari `pyproject.toml`:
```bash
pip install -e .
```

2. Jalankan server FastAPI:
```bash
python server.py
```

---

## 📖 Dokumentasi API

Buka browser Anda setelah server berjalan:
- **Swagger UI:** `http://localhost:8888/docs` (atau `http://localhost:8000/docs`)
- **ReDoc:** `http://localhost:8888/redoc`
- **OpenAPI Schema:** `http://localhost:8888/openapi.json`
