# users.py
import os
import time
import json
import traceback
from telebot import types
from anime import list_anime, ANIME_FILE
ANIME_FILE = "anime.json"
CHANNELS_FILE = "channels.json"

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
def user_main_menu(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📺 Animelar ro‘yxati")
    bot.send_message(
        message.chat.id,
        "🤖 Xush kelibsiz! Kerakli bo‘limni tanlang:",
        reply_markup=markup,
    )
def check_subscription(bot, user_id):
    """Foydalanuvchi kanallarga obuna ekanligini tekshiradi"""
    channels = load_json(CHANNELS_FILE)
    not_subscribed = []
    for ch in channels:
        try:
            username = ch["username"]
            if not username.startswith("@"):
                username = "@" + username
            member = bot.get_chat_member(username, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed.append(ch)
        except Exception:
            not_subscribed.append(ch)
    return not_subscribed

def is_subscribed_user(user_id, subscriptions):
    """Foydalanuvchi obuna aktivligini tekshiradi"""
    current_time = time.time()
    for sub in subscriptions:
        if sub.get("user_id") == user_id and sub.get("active") and sub.get("end_date", 0) > current_time:
            return True
    return False

def user_menu(bot, message):
    """Oddiy foydalanuvchi menyusi"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔍 Anime izlash", "📖 Qo'llanma")
    markup.add("📢 Reklama va homiylik")
    bot.send_message(message.chat.id, "👋 Salom! Quyidagi bo'limlardan birini tanlang:", reply_markup=markup)

def handle_user_steps(bot, message, user_states, subscriptions):
    user_id = message.from_user.id

    # 🔍 Anime izlash
    if message.text == "🔍 Anime izlash":
        not_subscribed = check_subscription(bot, user_id)
        if not_subscribed:
            markup = types.InlineKeyboardMarkup()
            for ch in not_subscribed:
                markup.add(types.InlineKeyboardButton(f"📡 {ch['name']}", url=f"https://t.me/{ch['username'].replace('@','')}"))
            bot.send_message(message.chat.id, "❌ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:", reply_markup=markup)
            return

        bot.send_message(message.chat.id, "🔎 Anime nomi yoki ID sini kiriting:")
        user_states[user_id] = {"step": "search", "step_type": "user_search"}
        return

    # 📖 Qo'llanma
    elif message.text == "📖 Qo'llanma":
        text = (
            "📖 <b>Qo‘llanma: New Dubbing botidan foydalanish</b>\n\n"
            "1. 🔍 Anime izlash — anime nomi yoki ID ni kiriting, rasm va qismlar chiqadi. \"⬇️ Yuklash\" tugmasi orqali barcha qismlarni yuklab olishingiz mumkin.\n"
            "2. 📢 Reklama va homiylik — reklama yoki homiylik uchun admin bilan bog‘laning.\n"
            "3. 📖 Qo‘llanma — ushbu yordam matni.\n\n"
            "ℹ️ <b>New Dubbing haqida</b>:\n"
            "Yangi ovozlangan animelar va qismlar to‘plami. Har bir anime uchun qismlar va videolar muntazam yangilanadi.\n"
            "Rasmiy kanal: t.me/NeW_TV_Rasmiy\n"
            "Admin: @MAXKAMOV_ADMIN1"
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        return

    # 📢 Reklama va homiylik
    elif message.text == "📢 Reklama va homiylik":
        not_subscribed = check_subscription(bot, user_id)
        if not_subscribed:
            markup = types.InlineKeyboardMarkup()
            for ch in not_subscribed:
                markup.add(types.InlineKeyboardButton(f"📡 {ch['name']}", url=f"https://t.me/{ch['username'].replace('@','')}"))
            bot.send_message(message.chat.id, "❌ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:", reply_markup=markup)
            return

        if is_subscribed_user(user_id, subscriptions):
            bot.send_message(message.chat.id, "📢 Reklama va homiylik uchun admin bilan bog'laning: @MAXKAMOV_ADMIN1")
        else:
            try:
                price = 10000
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("💳 To'lov qilish", callback_data="subscribe_payment"))
                bot.send_message(
                    message.chat.id, 
                    f"❗️ Reklama va homiylik uchun avval obuna bo'lishingiz kerak.\n\n💰 Obuna narxi: {price} so'm/oy", 
                    reply_markup=markup
                )
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Xatolik yuz berdi: {str(e)}")
        return

def user_search_step(bot, message):
    """Foydalanuvchi qidiruv bosqichi"""
    user_id = message.from_user.id
    query = message.text.strip().lower()
    anime_list = load_json(ANIME_FILE)
    results = []
    for a in anime_list:
        if query in a["name"].lower() or query == str(a["id"]):
            results.append(a)
    if results:
        for a in results:
            caption = (
                f"🎬 <b>{a['name']}</b>\n"
                f"📺 Sifat: {a.get('quality','-')}\n"
                f"🆔 ID: {a.get('id','-')}\n"
                f"🗣 Til: {a.get('language','-')}\n"
                f"🎭 Janr: {a.get('genre','-')}\n"
            )
            markup = types.InlineKeyboardMarkup()
            for ep in a.get("episodes", []):
                markup.add(
                    types.InlineKeyboardButton(
                        f"⬇️ {ep['number']}-qismni yuklab olish",
                        callback_data=f"download_{a['id']}_{ep['number']}"
                    )
                )
            bot.send_photo(message.chat.id, a.get("image"), caption=caption, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Hech narsa topilmadi.")
