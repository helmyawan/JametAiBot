# 🧠 JametAI Bot

JametAI adalah Discord Bot berbasis Python (`discord.py`) dan AI (LLM) yang didesain memiliki kepribadian hardcore khas gabungan Suroboyoan & Jogjaan. Kerjanya misuh-misuh, ngomel-ngomel (Jancok, Asu, Bajilak), tapi kalau ngasih solusi codingan dijamin *best practice* 100%.

Bot ini didesain khusus untuk diam di **satu channel tertentu** (contoh: `#tanya-jamet`). Saat user membuat *Thread* di channel tersebut, JametAI akan langsung me-*mention* pembuat thread, dan percakapan (beserta konteks AI-nya) berjalan eksklusif di dalam thread itu saja.

---

## 🔥 Fitur Utama

- **Suroboyo-Jogja Hardcore Persona**: Memiliki kamus 500+ variasi kata kasar/sarkas untuk menyemprot user yang nanyanya gak jelas atau kodenya berantakan (bisa dibaca di `soul.md`).
- **Thread-Based Context**: Percakapan dibatasi di thread agar channel Discord tetap bersih. Tiap thread punya isolasi memory history masing-masing.
- **Global User Reputation (Memory)**: Bot mengingat seberapa pintar/bodoh usernya. SQLite merekam *note* rahasia per `user_id` di background, jadi bot tau jika user sering mengulangi kesalahan yang sama.
- **File Attachment Reader**: User bisa drag-and-drop kode `.py, .js, .json, .txt` dll (Maks 50KB), bot bisa baca isinya dan me-review-nya.
- **Dynamic Sarcastic Status**: Activity status bot (Watching, Playing, Listening) akan berputar secara random tiap 30 menit dari 500+ kombinasi tulisan sarkas (contoh: *Watching kodinganmu sing bosok*).
- **UX Typing Delay**: Response panjang dari LLM yang terpotong Discord 2000 chars limit akan dikirim dengan delay *typing indicator* supaya terasa lebih "nyata".

- **Reaction UX (👀 -> ✅/❌)**: Memberikan feedback visual instan saat pesan sedang diproses dan saat selesai.
- **Auto-Archiver**: Membersihkan thread yang tidak aktif lebih dari 3 hari (72 jam) secara otomatis dengan pesan sarkas perpisahan.
- **Senior Dev Mode**: Opsi strict mode (`SENIOR_DEV_MODE=True`). Jika diaktifkan, bot akan menolak keras permintaan membuat aplikasi utuh dari nol dan menyuruh user belajar nulis kode sendiri.

---

## 💻 Slash Commands

JametAI dilengkapi dengan Slash Commands Discord untuk monitoring dan moderasi:

| Command | Fungsi | Akses |
|---|---|---|
| `/jamet_ping` | Cek latensi Discord & LLM | Semua User |
| `/jamet_rep [@user]` | Cek profil reputasi user (Skor, Tier, Catatan) | Semua User |
| `/jamet_status` | Cek Uptime bot, jumlah user diingat, dan total thread | Semua User |
| `/jamet_topbodoh` | Papan klasemen 5 user dengan skor paling minus | Semua User |
| `/jamet_toppinter` | Papan klasemen 5 user dengan skor paling plus | Semua User |
| `/jamet_clear_thread` | Menghapus amnesia history percakapan di thread terkait | **Admin Only** |
| `/jamet_reset @user` | Menghapus semua memory & dosa reputasi user dari DB | **Admin Only** |

---

## 🎮 Cara Pakai (Untuk User Discord)

Biar user-mu nggak bingung, *copy-paste* panduan di bawah ini dan taruh di channel *Rules* atau di-pin di channel tempat JametAI nongkrong:

```text
**🔥 CARA MAKAI BOT JAMET AI 🔥**

Bot ini cuma bakal ngerespon kalau kamu nanya di dalam **THREAD**, bukan nge-chat langsung di channel! Biar rapi cok.

**Langkah-langkah:**
1. Di channel ini, klik icon **[+]** atau **Create Thread** (di pojok kanan atas / di message bar).
2. Kasih nama thread sesuai topik error/pertanyaanmu (misal: "Error Python DB", "Review Kode React").
3. Begitu thread kebuat, JametAI bakal otomatis nyapa kamu duluan.
4. Langsung tanyain aja masalahmu di dalam thread itu! JametAI bakal langsung mikir (keliatan react 👀).

**Rules Tambahan:**
- **Bisa baca file!** Kamu bisa langsung drag-and-drop file kodemu (.py, .js, .txt, dll - max 50KB) ke dalam thread. Nggak usah copas kodingan kepanjangan.
- **Jangan spam.** Ada cooldown 5 detik tiap ngetik. Nekat spam? Siap-siap di-banned.
- **Bot punya memori reputasi.** Kalau kamu nanya bagus, skormu naik. Kalau nanya bodoh atau muter-muter, skormu minus dan bot bakal makin kasar ngegasnya.
- **Senior Dev Mode.** Jangan nyuruh bot bikin aplikasi full dari nol! Dia bakal nolak. Minta tolong review atau cari bug aja.
- Thread yang mati (nggak ada yang ngetik) lebih dari 3 hari bakal otomatis ditutup sama bot.
```

---

## 🛠 Instalasi & Setup

### Persyaratan
- Python 3.11+
- API Key LLM (OpenAI-compatible)

### Langkah Install
1. Clone repo ini:
   ```bash
   git clone https://github.com/helmyawan/JametAiBot.git
   cd JametAiBot
   ```
2. Buat Virtual Environment (opsional tapi disarankan):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Mac/Linux
   ```
3. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Setup konfigurasi `.env`:
   - Rename `.env.example` ke `.env`.
   - Buka dan isi file `.env`:
     ```ini
     DISCORD_TOKEN=token_bot_discord_kalian
     CHANNEL_ID=id_channel_tempat_bot_nangkring
     LLM_API_URL=http://.../v1/chat/completions
     LLM_API_KEY=sk-...
     LLM_MODEL=JametAI
     LLM_TIMEOUT=30
     RATE_LIMIT_SECONDS=5
     MAX_HISTORY=20
     ```

---

## 🚀 Cara Menjalankan

Jalankan script utamanya:
```bash
python bot.py
```

*Jika jalan di VPS (production), sangat disarankan menggunakan `PM2` atau `systemd`.*
```bash
# Contoh dengan PM2
pm2 start bot.py --name jametai --interpreter python3
```

---

## 🏗 Struktur Proyek
- `bot.py` : Entry point bot, load *Cogs*.
- `config.py` : Load & mapping *env vars*.
- `database.py` : Logic *aiosqlite* (history per-thread & reputasi user).
- `soul.md` : System prompt rahasia yang mendefinisikan persona JametAI.
- `cogs/`
  - `thread_handler.py` : Menyapa user otomatis waktu thread baru dibuat.
  - `ai_handler.py` : Komunikasi ke LLM, rate-limiter, chunk splitter, memory injector.
  - `status_handler.py` : Background loop status Discord 500+ variasi.
  - `archiver_handler.py` : Background task auto-archive thread non-aktif.
  - `slash_commands.py` : Definisi UI Slash Commands & integrasi API Discord.
  - `error_handler.py` : Mencegah error spam & silent fail.
