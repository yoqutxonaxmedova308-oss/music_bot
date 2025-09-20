from dotenv import load_dotenv
import os
import time
import telebot
from telebot import types
import json
import traceback
from utils import check_subscription,is_admin
from subscriptions import send_subscription_prompt, SUBSCRIPTIONS_FILE, CHANNELS_FILE
from admin import admin_panel_menu, handle_admin_steps
from users import user_main_menu, handle_user_steps




# --- ENV yuklash ---
load_dotenv()
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]

bot = telebot.TeleBot(TOKEN)

# --- Fayllar ---
ANIME_FILE = "anime.json"
CHANNELS_FILE = "channels.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"

USER_STATES = {}  # <-- Konsistent nom

# --- Yordamchi funksiyalar ---
def load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"JSON faylini o'qishda xatolik: {e}")
        print(traceback.format_exc())
        return []

def save_json(file, data):
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"JSON saqlashda xatolik: {e}")
        print(traceback.format_exc())

def load_channels():
    return load_json(CHANNELS_FILE)

def save_channels(channels):
    save_json(CHANNELS_FILE, channels)

def get_subscriptions():
    data = load_json(SUBSCRIPTIONS_FILE)
    if isinstance(data, dict):
        return data.get("subscriptions", [])
    return data

def save_subscriptions(subscriptions):
    data = load_json(SUBSCRIPTIONS_FILE)
    if not isinstance(data, dict):
        data = {}
    data["subscriptions"] = subscriptions
    save_json(SUBSCRIPTIONS_FILE, data)

def get_subscription_price():
    data = load_json(SUBSCRIPTIONS_FILE)
    return data.get("price", 10000)

def set_subscription_price(price):
    data = load_json(SUBSCRIPTIONS_FILE)
    data["price"] = price
    data.setdefault("subscriptions", [])
    save_json(SUBSCRIPTIONS_FILE, data)

def is_admin(user_id):
    return user_id in ADMINS

def is_subscribed(user_id, channel_username):
    try:
        if not channel_username.startswith('@'):
            channel_username = '@' + channel_username
        member = bot.get_chat_member(channel_username, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Obuna tekshirishda xatolik: {e}")
        return False

def is_subscribed_user(user_id):
    subs = get_subscriptions()
    current_time = time.time()
    for sub in subs:
        if sub.get("user_id") == user_id and sub.get("active") and sub.get("end_date", 0) > current_time:
            return True
    return False

def check_subscription(user_id):
    channels = load_channels()
    not_subscribed = []
    for ch in channels:
        try:
            if not is_subscribed(user_id, ch["username"]):
                not_subscribed.append(ch)
        except Exception:
            continue
    return not_subscribed

def cleanup_unused_files():
    anime_list = load_json(ANIME_FILE)
    used_files = []
    for a in anime_list:
        used_files.append(a.get("image", ""))
        for ep in a.get("episodes", []):
            used_files.append(ep.get("video", ""))
    for folder in ["uploads/images", "uploads/videos"]:
        if os.path.exists(folder):
            import glob
            for f in glob.glob(os.path.join(folder, "*")):
                if os.path.basename(f) not in [os.path.basename(u) for u in used_files]:
                    try:
                        os.remove(f)
                        print(f"❌ Keraksiz fayl o'chirildi: {f}")
                    except Exception as e:
                        print(traceback.format_exc())

# --- Menyular ---
def user_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔍 Anime izlash", "📖 Qo'llanma")
    markup.add("📢 Reklama va homiylik")
    bot.send_message(message.chat.id, "👋 Salom! Quyidagi bo'limlardan birini tanlang:", reply_markup=markup)

def admin_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Statistika", "🎬 Anime sozlash")
    markup.add("👨‍💻 Adminlar", "📡 Kanallar") 
    markup.add("💎 Obunani boshqarish", "📤 Anime kanalga joylash")
    bot.send_message(message.chat.id, "🔐 Admin paneliga xush kelibsiz!", reply_markup=markup)
    user_id = message.from_user.id
    user_states.pop(user_id, None)

def channels_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Kanal qo'shish", "❌ Kanal o'chirish")
    markup.add("📋 Kanallar ro'yxati", "🔙 Orqaga")
    bot.send_message(message.chat.id, "📡 Kanallar bo'limi:", reply_markup=markup)

def anime_settings_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Anime qo'shish", "🎞 Qism qo'shish")
    markup.add("✏️ Tahrirlash", "🔙 Orqaga")
    bot.send_message(message.chat.id, "🎬 Anime sozlash bo'limi:", reply_markup=markup)
    user_states.pop(message.from_user.id, None)

def adminlar_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Admin qo'shish", "❌ Admin o'chirish")
    markup.add("📋 Adminlar ro'yxati", "🔙 Orqaga")
    bot.send_message(message.chat.id, "👨‍💻 Adminlar bo'limi:", reply_markup=markup)

def subscription_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Obuna narxini o'zgartirish", "➕ Foydalanuvchini obuna qilish")
    markup.add("📋 Obunalar ro'yxati", "🔙 Orqaga")
    bot.send_message(message.chat.id, "💎 Obuna boshqaruvi:", reply_markup=markup)

# --- Bot ishga tushirish ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        bot.send_message(message.chat.id, "👑 Admin sifatida xush kelibsiz!")
        admin_menu(message)  # 🔹 Admin menyusini chiqaramiz
    else:
        bot.send_message(message.chat.id, "🙂 Oddiy foydalanuvchi sifatida kirdingiz.")
        user_menu(message)   # 🔹 Oddiy foydalanuvchi menyusi


@bot.message_handler(func=lambda m: m.text == "📡 Kanallar")
def show_channels_menu(message):
    channels_menu(message)

@bot.message_handler(func=lambda m: m.text == "🎬 Anime sozlash")
def show_anime_settings_menu(message):
    anime_settings_menu(message)

@bot.message_handler(func=lambda m: m.text == "👨‍💻 Adminlar")
def show_adminlar_menu(message):
    adminlar_menu(message)

@bot.message_handler(func=lambda m: m.text == "💎 Obunani boshqarish")
def show_subscription_menu(message):
    subscription_menu(message)

@bot.message_handler(func=lambda m: True)
def all_messages(message):
    user_id = message.from_user.id
    if is_admin(user_id, ADMINS):
         handle_admin_steps(bot, message, USER_STATES)
    else:
        bot.send_message(message.chat.id, "❌ Sizda admin huquqi yo‘q!")

if __name__ == "__main__":
    cleanup_unused_files()
    print("🤖 Bot ishga tushdi...")
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"❌ Bot xatolik yuz berdi: {e}")
        import time
        time.sleep(5)
        bot.infinity_polling(skip_pending=True)
