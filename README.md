# Aplikasi CRUD Data Mahasiswa

UTS Lab Pemrograman — Departemen Bisnis Digital, Universitas Diponegoro.

Aplikasi web sederhana untuk mengelola data mahasiswa (Create, Read, Update, Delete).

## Teknologi
- Backend: Python + Flask
- Database: SQLite (file `mahasiswa.db`, dibuat otomatis saat pertama dijalankan)
- Frontend: HTML + form (Jinja2 templates)

## Fitur
- **Create** — tambah mahasiswa lewat form
- **Read** — daftar mahasiswa (tabel) dan halaman detail, plus pencarian
- **Update** — ubah data mahasiswa (NIM tidak dapat diubah)
- **Delete** — hapus data mahasiswa (dengan konfirmasi)
- **Validasi** — NIM/nama/program studi wajib diisi, IPK harus 0.00–4.00, NIM duplikat ditolak
- **Lama Studi** (tahun) = tahun sekarang − angkatan, dihitung otomatis oleh program
- Data tersimpan permanen di database SQLite

## Cara Menjalankan
```bash
python -m venv venv
# Windows: venv\Scripts\activate    |  Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Buka http://127.0.0.1:5000

## Struktur Proyek
```
.
├── app.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── form.html
│   └── detail.html
└── mahasiswa.db   (dibuat otomatis)
```

## Skema Tabel `mahasiswa`
| Field | Tipe | Keterangan |
|---|---|---|
| nim | INTEGER | primary key / unique |
| nama | TEXT | wajib diisi |
| program_studi | TEXT | wajib diisi |
| angkatan | INTEGER | wajib diisi |
| ipk | REAL | wajib diisi (0.00–4.00) |
