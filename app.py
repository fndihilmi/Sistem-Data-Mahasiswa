import math
import os
import sqlite3
from datetime import datetime

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "mahasiswa.db")

app = Flask(__name__)
app.secret_key = "ganti-dengan-secret-key-anda"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS mahasiswa (
            nim           INTEGER PRIMARY KEY,
            nama          TEXT    NOT NULL,
            program_studi TEXT    NOT NULL,
            angkatan      INTEGER NOT NULL,
            ipk           REAL    NOT NULL
        )
        """
    )
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def tahun_sekarang():
    return datetime.now().year


def tambah_lama_studi(row):
    """Ubah sqlite Row menjadi dict + Lama Studi (dihitung program)."""
    data = dict(row)
    data["lama_studi"] = tahun_sekarang() - data["angkatan"]
    return data


def validasi_form(form, cek_nim=True):
    """Validasi input form. Mengembalikan (data, daftar_error)."""
    errors = []
    nim_raw = (form.get("nim") or "").strip()
    nama = (form.get("nama") or "").strip()
    program_studi = (form.get("program_studi") or "").strip()
    angkatan_raw = (form.get("angkatan") or "").strip()
    ipk_raw = (form.get("ipk") or "").strip().replace(",", ".")

    nim = None
    if cek_nim:
        if not nim_raw:
            errors.append("NIM wajib diisi.")
        else:
            try:
                nim = int(nim_raw)
                if nim <= 0:
                    errors.append("NIM harus berupa bilangan bulat positif.")
            except ValueError:
                errors.append("NIM harus berupa angka (bilangan bulat).")

    if not nama:
        errors.append("Nama wajib diisi.")
    if not program_studi:
        errors.append("Program studi wajib diisi.")

    angkatan = None
    if not angkatan_raw:
        errors.append("Angkatan wajib diisi.")
    else:
        try:
            angkatan = int(angkatan_raw)
            if angkatan < 1900 or angkatan > tahun_sekarang():
                errors.append(f"Angkatan harus antara 1900 dan {tahun_sekarang()}.")
        except ValueError:
            errors.append("Angkatan harus berupa angka (bilangan bulat).")

    ipk = None
    if not ipk_raw:
        errors.append("IPK wajib diisi.")
    else:
        try:
            ipk = float(ipk_raw)
            if math.isnan(ipk) or math.isinf(ipk) or ipk < 0.0 or ipk > 4.0:
                errors.append("IPK harus berada di rentang 0.00 - 4.00.")
        except ValueError:
            errors.append("IPK harus berupa angka (contoh: 3.75).")

    data = {
        "nim": nim if nim is not None else nim_raw,
        "nama": nama,
        "program_studi": program_studi,
        "angkatan": angkatan if angkatan is not None else angkatan_raw,
        "ipk": ipk if ipk is not None else ipk_raw,
    }
    return data, errors


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """READ (daftar): tampilkan seluruh mahasiswa + Lama Studi."""
    q = (request.args.get("q") or "").strip()
    db = get_db()
    if q:
        like = f"%{q}%"
        rows = db.execute(
            "SELECT * FROM mahasiswa WHERE CAST(nim AS TEXT) LIKE ? "
            "OR nama LIKE ? OR program_studi LIKE ? ORDER BY nim",
            (like, like, like),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM mahasiswa ORDER BY nim").fetchall()
    mahasiswa = [tambah_lama_studi(r) for r in rows]
    return render_template("index.html", mahasiswa=mahasiswa, q=q)


@app.route("/tambah", methods=["GET", "POST"])
def tambah():
    """CREATE: tambah mahasiswa baru."""
    if request.method == "POST":
        data, errors = validasi_form(request.form, cek_nim=True)
        if not errors:
            db = get_db()
            ada = db.execute(
                "SELECT 1 FROM mahasiswa WHERE nim = ?", (data["nim"],)
            ).fetchone()
            if ada:
                errors.append(f"NIM {data['nim']} sudah terdaftar.")
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("form.html", mode="tambah", data=data), 400

        try:
            db.execute(
                "INSERT INTO mahasiswa (nim, nama, program_studi, angkatan, ipk) "
                "VALUES (?, ?, ?, ?, ?)",
                (data["nim"], data["nama"], data["program_studi"],
                 data["angkatan"], data["ipk"]),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash(f"NIM {data['nim']} sudah terdaftar.", "error")
            return render_template("form.html", mode="tambah", data=data), 400

        flash("Mahasiswa baru berhasil ditambahkan.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", mode="tambah", data={})


@app.route("/mahasiswa/<int:nim>")
def detail(nim):
    """READ (detail)."""
    row = get_db().execute(
        "SELECT * FROM mahasiswa WHERE nim = ?", (nim,)
    ).fetchone()
    if row is None:
        flash("Data mahasiswa tidak ditemukan.", "error")
        return redirect(url_for("index"))
    return render_template("detail.html", m=tambah_lama_studi(row))


@app.route("/mahasiswa/<int:nim>/edit", methods=["GET", "POST"])
def edit(nim):
    """UPDATE: ubah data mahasiswa (NIM tidak dapat diubah)."""
    db = get_db()
    row = db.execute("SELECT * FROM mahasiswa WHERE nim = ?", (nim,)).fetchone()
    if row is None:
        flash("Data mahasiswa tidak ditemukan.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        data, errors = validasi_form(request.form, cek_nim=False)
        data["nim"] = nim
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("form.html", mode="edit", data=data), 400

        db.execute(
            "UPDATE mahasiswa SET nama = ?, program_studi = ?, angkatan = ?, "
            "ipk = ? WHERE nim = ?",
            (data["nama"], data["program_studi"], data["angkatan"],
             data["ipk"], nim),
        )
        db.commit()
        flash("Data mahasiswa berhasil diperbarui.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", mode="edit", data=dict(row))


@app.route("/mahasiswa/<int:nim>/hapus", methods=["POST"])
def hapus(nim):
    """DELETE: hapus data mahasiswa."""
    db = get_db()
    cur = db.execute("DELETE FROM mahasiswa WHERE nim = ?", (nim,))
    db.commit()
    if cur.rowcount:
        flash("Data mahasiswa berhasil dihapus.", "success")
    else:
        flash("Data mahasiswa tidak ditemukan.", "error")
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
