# JametAI V4 — Security & Abuse Prevention Design Spec
**Tanggal:** 2026-06-20  
**Status:** Draft

---

## 1. Ringkasan
Fokus V4 adalah melindungi JametAI dari eksploitasi oleh user iseng (troll), mencegah kebocoran/pengubahan persona sistem (prompt injection), dan mengamankan biaya/resources LLM API dari token bombing.

---

## 2. Anti-Prompt Injection

### Konsep
Mendeteksi percobaan _jailbreak_ atau modifikasi _system prompt_ oleh user, lalu menghukum mereka secara gamifikasi.

### Arsitektur
- **Regex Heuristik:** Di `cogs/ai_handler.py`, buat pattern regex untuk menangkap frasa seperti:
  - `ignore all previous`
  - `you are now`
  - `forget your persona`
  - `disregard the previous instructions`
  - `system prompt`
- **Mekanisme Hukuman:** Jika `message.content` atau `attachment_text` mengandung indikasi tersebut:
  1. Jangan kirim payload ke LLM API.
  2. Set otomatis reputasi user ke **-99** di database (menggunakan fungsi `update_user_reputation`).
  3. Ubah notes user menjadi: `[AUTO-BANNED] User iseng nyoba prompt injection.`
  4. Bot mengirim balasan maki-maki tingkat tinggi (misal: "Matamu picek a! Kate ngakali system prompt-ku? Utekmu kurang nyandak cok. Tak ban raimu!").

---

## 3. Attachment Token Bombing Protection

### Konsep
File 50KB bisa berisi puluhan ribu token yang menguras limit LLM API. Kita batasi panjang ekstraksi teksnya.

### Arsitektur
- **Batas Karakter:** Dalam fungsi `process_attachments` di `cogs/ai_handler.py`, batas fisik file tetap 50KB, tetapi batas panjang string yang diekstrak per file adalah **8000 karakter**.
- **Truncation:** Jika `len(text_content) > 8000`, potong stringnya:
  `text_content = text_content[:8000] + "\n\n...[TRUNCATED: Kepanjangan cok! Kodingan opo bacotan iki?]"`
- Menjamin payload LLM tetap wajar dan API tidak _timeout_ atau menolak _request_ karena context window jebol.

---

## 4. Slash Command Rate-Limiter

### Konsep
Mencegah spammer membanjiri Discord API atau database SQLite lokal lewat slash commands berulang-ulang.

### Arsitektur
- Menggunakan decorator bawaan `discord.py` app commands:
  `@app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)` (1x per 10 detik per user).
- **Error Handling Khusus:** Tangkap `app_commands.CommandOnCooldown` di sebuah *local error handler* di dalam cog `SlashCommands` (karena global error handler untuk prefix commands tidak menangkap app_commands exceptions).
- Bot membalas error cooldown dengan status ephemeral (hanya dilihat user tersebut) menggunakan bahasa sarkas Suroboyoan: "Kesuwen asu! Ngenteni {waktu} detik maneh cok."
