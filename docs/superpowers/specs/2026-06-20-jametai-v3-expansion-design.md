# JametAI V3 — Expansion Design Spec
**Tanggal:** 2026-06-20  
**Status:** Draft

---

## 1. Ringkasan
Upgrade fungsionalitas JametAI ke V3. Menambahkan Auto-Archiver Thread, Behavior Senior Dev Mode, Gamified Reputation Score, Reaction Indicators (👀 -> ✅), dan Slash Commands lengkap (utilities, moderation, leaderboards).

---

## 2. Reaction Indicators (UX)

### Konsep
Memberikan visual cue kepada user bahwa pesan mereka sedang diproses, lalu menandai bahwa proses selesai. Ini melengkapi typing delay UX yang sudah ada.

### Mekanisme
Di dalam `on_message` pada `cogs/ai_handler.py`:
1. Sesaat setelah pesan lolos trigger dan rate limit, bot menambahkan reaksi 👀 ke pesan tersebut (`await message.add_reaction("👀")`).
2. Proses LLM dan *chunking* berjalan seperti biasa.
3. Setelah respons terkirim sepenuhnya, bot menghapus reaksi 👀 (`await message.remove_reaction("👀", bot.user)`) lalu menambahkan reaksi ✅ (`await message.add_reaction("✅")`).
4. Jika terjadi error API, hapus 👀 dan tambahkan ❌.

---

## 3. Auto-Archiver (UX/Tidiness)

### Konsep
Menjaga channel Discord tetap bersih dari thread mati. Jika thread di `CHANNEL_ID` tidak memiliki aktivitas (pesan baru) lebih dari **3 hari (>72 jam)**, bot akan mengarsipkan thread tersebut secara otomatis.

### Arsitektur
- **File baru:** `cogs/archiver_handler.py`.
- **Mekanisme:** Menggunakan `discord.ext.tasks` yang berjalan setiap 6 jam. Loop akan memindai semua active threads di `CHANNEL_ID`.
- **Pesan Perpisahan:** Bot mengirim pesan sarkas (misal: "Wes 3 dino ra ono sing ngomong, thread iki tak kubur. Modyar o kono.") sebelum mengeset `thread.edit(archived=True)`.

---

## 4. Senior Dev Mode (Behavior)

### Konsep
JametAI bertindak sebagai Senior Dev tulen. Tidak mau diminta membuat aplikasi/script full dari nol ("write me a full app"). Hanya melayani debugging, review kode, atau penjelasan konsep.

### Arsitektur
- **Konfigurasi:** Tambah `SENIOR_DEV_MODE=True` di `.env` dan `config.py`.
- **Implementasi:** Di-inject ke system prompt (`SOUL_PROMPT`). Jika aktif, prompt ditambahkan: *"TOLAK PERMINTAAN membuat kode dari nol atau membuat aplikasi utuh. Maki user karena malas, dan suruh mereka nulis kode sendiri lalu kasih ke kamu untuk di-review."*

---

## 5. Gamified Reputation Score

### Konsep
Selain notes teks (V2), user sekarang punya `score` bertipe integer. Nanya bagus/pintar = score naik (+1). Nanya bodoh/diulang-ulang = score turun (-1). Score mempengaruhi tingkat kekasaran balasan bot.

### Arsitektur
- **DB Schema:** Tambah kolom `score INTEGER DEFAULT 0` pada tabel `user_reputation`.
- **Updater:** Background task V2 `_update_reputation_bg` diperbarui instruksinya. Selain notes, LLM harus mereturn JSON/string format seperti `SCORE_MODIFIER: +1` atau `SCORE_MODIFIER: -1`.
- **Tier (berdasarkan Score):**
  - Score >= +5 : "Suhu / Pinter" (Lebih respek, jarang dimaki)
  - Score -4 s/d +4 : "Biasa / Ndes" (Default)
  - Score <= -5 : "Goblok Akut / Beban Tim" (Sangat agresif/kasar)
- Tier dan score di-inject ke system prompt.

---

## 6. Slash Commands (`cogs/slash_commands.py`)

Gunakan fitur `app_commands` bawaan `discord.py` v2. Sinkronisasi tree pada saat `setup_hook`.

Daftar Command:

| Command | Args | Akses | Fungsi & Respon Bot |
|---|---|---|---|
| `/jamet_ping` | - | Semua | "Pong asu! Latensi X ms. LLM Latensi Y ms." |
| `/jamet_rep` | `user` (opsional) | Semua | Menampilkan profil reputasi (notes, score, tier) user. |
| `/jamet_reset` | `user` (wajib) | Admin Only (`@app_commands.checks.has_permissions(administrator=True)`) | Hapus memory & reset score user jadi 0. |
| `/jamet_status` | - | Semua | Uptime bot, jumlah thread aktif, jumlah user terdaftar di DB. |
| `/jamet_clear_thread` | - | Admin Only | Hapus semua pesan di `chat_history` DB untuk thread yang sedang dibuka. |
| `/jamet_topbodoh` | - | Semua | Leaderboard 5 user dengan score terendah (negatif tertinggi). |
| `/jamet_toppinter` | - | Semua | Leaderboard 5 user dengan score tertinggi. |

---

## 7. Persyaratan Modifikasi File
- `bot.py`: Tambah load extension `cogs.archiver_handler` dan `cogs.slash_commands`. Jangan lupa panggil `await self.tree.sync()`.
- `config.py`: Load `SENIOR_DEV_MODE`.
- `database.py`: Migrasi tabel `user_reputation` tambah kolom `score`. Tambah query leaderboard.
- `cogs/ai_handler.py`: Update logic prompt `_update_reputation_bg` untuk support *scoring*.
- `cogs/slash_commands.py`: Cog baru.
- `cogs/archiver_handler.py`: Cog baru.
