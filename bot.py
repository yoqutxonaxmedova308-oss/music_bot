# bot.py
import os
import shutil
import tempfile
import subprocess
import uuid
import telebot
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

# --- ENV yuklash ---
load_dotenv()
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = telebot.TeleBot(TOKEN)

# Foydalanuvchilarning URL-larini vaqtinchalik saqlash
user_links = {}

# --- YT-DLP CONFIG ---
YTDL_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": "%(id)s.%(ext)s",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "geo_bypass": True,
}

# --- Yuklab olish funksiyasi ---
def download_from_url(url: str, target_dir: str):
    ydl_opts = YTDL_OPTS.copy()
    ydl_opts["outtmpl"] = os.path.join(target_dir, "%(id)s.%(ext)s")
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename, info

# --- MP3 konvertatsiya ---
def convert_to_mp3(input_path: str, output_path: str):
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd, check=True)

# --- /start ---
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    if message.from_user.id == OWNER_ID:
        markup.row("📊 Statistika", "📝 Foydalanuvchilar")
        markup.row("⚙️ Bot sozlamalari", "🎵 Musiqa yuklash")
        bot.send_message(message.chat.id, "Salom Admin! 👑", reply_markup=markup)
    else:
        markup.row("🎵 Musiqa yuklash")
        bot.send_message(message.chat.id, "Salom! 🎧 Musiqa yuklash tugmasini bosing.", reply_markup=markup)

# --- Tugmalar handleri (faqat tugmalar: Statistika, Foydalanuvchilar, Sozlamalar) ---
@bot.message_handler(func=lambda m: m.from_user.id == OWNER_ID and m.text in ["📊 Statistika", "📝 Foydalanuvchilar", "⚙️ Bot sozlamalari"])
def admin_panel(message):
    if message.text == "📊 Statistika":
        total_users = len(user_links)
        bot.send_message(message.chat.id, f"📊 Bot statistika:\n\n👥 Faol foydalanuvchilar: {total_users}\n🎵 Yuklangan audio fayllar: {total_users}")
    elif message.text == "📝 Foydalanuvchilar":
        text = "Foydalanuvchilar:\n" + "\n".join(user_links.keys()) if user_links else "Hozircha foydalanuvchilar yo‘q."
        bot.send_message(message.chat.id, text)
    elif message.text == "⚙️ Bot sozlamalari":
        bot.send_message(message.chat.id, "⚙️ Bot sozlamalari: Bu yerga sozlamalarni qo‘shishingiz mumkin.")

# --- Musiqa yuklash tugmasi (admin va foydalanuvchi uchun bir xil) ---
@bot.message_handler(func=lambda m: m.text == "🎵 Musiqa yuklash")
def request_link(message):
    bot.send_message(message.chat.id, "🎵 Link yuboring, men audio yuklab beraman.")

# --- Link yuborilganda ishlovchi handler ---
@bot.message_handler(func=lambda m: any(x in m.text for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]))
def handle_link(message):
    url = message.text.strip()
    unique_id = str(uuid.uuid4())
    user_links[unique_id] = url

    bot.send_message(message.chat.id, "⏳ Yuklanmoqda, biroz kuting...")
    tmpdir = tempfile.mkdtemp(prefix="media_dl_")

    try:
        filepath, info = download_from_url(url, tmpdir)
        title = info.get("title", "Fayl")
        performer = info.get("uploader") or info.get("artist") or "Unknown"

        mp3_path = os.path.join(tmpdir, f"{info.get('id')}.mp3")
        try:
            convert_to_mp3(filepath, mp3_path)
            send_path = mp3_path
        except Exception:
            send_path = filepath

        with open(send_path, "rb") as f:
            bot.send_chat_action(message.chat.id, "upload_audio")
            bot.send_audio(message.chat.id, f, title=title, performer=performer)

        bot.send_message(message.chat.id, "🎵 Musiqa yuborildi!")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xatolik yuz berdi: {e}")
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass
        user_links.pop(unique_id, None)



if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling()
