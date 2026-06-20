# JametAI V2 — Enhancement Design Spec
**Tanggal:** 2026-06-20  
**Status:** Draft

---

## 1. Ringkasan
Upgrade fungsionalitas JametAI untuk meningkatkan UX, kepribadian, dan kapabilitas problem solving. Terdiri dari 4 fitur utama: Dynamic Status (500+ variasi), Enhanced Typing UX, File Reader (text/code), dan Global User Memory berbasis SQLite.

---

## 2. Dynamic Status & Persona (500+ Frasa)

### Konsep
Bot merotasi status Discord (`discord.Activity`) setiap X menit dengan 500+ kalimat sarkas.

### Arsitektur
- **File baru:** `cogs/status_handler.py`.
- **Komponen:** Menggunakan `discord.ext.tasks` loop.
- **Data Source:** Sebuah file JSON atau konstanta Python `status_list.py` yang berisi generator 500+ variasi kalimat status (Playing, Watching, Listening) dengan vibe Suroboyo-Jogja.

---

## 3. Enhanced UX (Typing Indicator)

### Konsep
Memperkuat impresi bahwa bot benar-benar mengetik dan mikir.

### Arsitektur
- Sudah menggunakan `async with message.channel.typing()` di `call_llm`.
- Tambahan: Saat bot memotong pesan >2000 karakter, tambahkan `await asyncio.sleep(1)` + `typing()` sebelum mengirim chunk berikutnya agar tidak instan (spam).

---

## 4. File / Code Reader

### Konsep
Bot dapat menerima attachment `.py, .js, .txt`, dll dari user dan membaca isinya sebagai bagian dari input context LLM.

### Arsitektur
- Di dalam `on_message` (`ai_handler.py`), cek `message.attachments`.
- **Filter Ekstensi:** `.py, .js, .ts, .html, .css, .txt, .json, .md, .csv`. Tolak `.jpg, .png, .exe, .zip`, dll.
- **Filter Ukuran:** Maks 50KB. Jika lebih, tolak dengan makian kasar.
- **Processing:** Download isi file secara async (`aiohttp`), gabungkan (inject) ke `message.content` sebelum masuk ke DB history dan payload LLM.

---

## 5. Global User Memory (Reputasi User)

### Konsep
Mengingat reputasi atau trait user (bodoh, pintar, spammer, dsb) lintas-thread.

### Arsitektur
- **Skema DB (Tabel baru: `user_reputation`)**:
  `user_id TEXT PK, notes TEXT, updated_at DATETIME`
- **Integrasi LLM Input:**
  Setiap request dari user X, bot akan mengambil data `notes` dari DB.
  Inject ke system prompt: `[INFO: Kamu punya ingatan tentang user ini: {notes}]`.
- **Mekanisme Update Memory:**
  Untuk menghemat token dan response time, update memory tidak dilakukan di pass utama. Alih-alih, setelah merespons, bot menjalankan *background task* (fire-and-forget) yang mengirim history terbaru ke LLM dengan instruksi spesifik:
  *"Ekstrak sifat/skill/kesalahan dominan user ini dalam 1-2 kalimat padat. Jika tidak ada yang penting, jawab KOSONG."*
  Hasilnya akan meng-update/overwrite `notes` di tabel `user_reputation`.

---

## 6. Integrasi Keseluruhan

1. `status_handler.py` -> Membutuhkan dependensi generator 500 status.
2. `database.py` -> Tambah fungsi `init_user_rep_db()`, `get_user_rep()`, `update_user_rep()`.
3. `ai_handler.py` -> Tambah logic download attachment, inject user rep, trigger async rep-update.

Tidak ada perubahan struktur deployment atau dependencies baru.
