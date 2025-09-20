import json
import os
import time
import traceback
from dotenv import load_dotenv

# .env ni yuklash
load_dotenv()

# ================== ADMIN TEKSHIRISH ==================
ADMINS = os.getenv("ADMINS", "")

# Ro‘yxatga aylantirish
if ADMINS:
    ADMINS = [int(x.strip()) for x in ADMINS.split(",") if x.strip().isdigit()]
else:
    ADMINS = []

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi adminmi-yo‘qmi tekshiradi"""
    return user_id in ADMINS


# ================== JSON FAYL O‘QISH / SAQLASH ==================
def load_json(file_path):
    """JSON faylini o‘qish, mavjud bo‘lmasa bo‘sh ro‘yxat qaytaradi"""
    try:
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ JSON o'qishda xatolik: {e}")
        print(traceback.format_exc())
        return []

def save_json(file_path, data):
    """JSON faylga saqlash"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ JSON saqlashda xatolik: {e}")
        print(traceback.format_exc())


# ================== ODDIY FOYDALANUVCHI OBUNASI ==================
def is_subscribed(user_id, subscriptions):
    """Foydalanuvchi obuna ekanligini tekshiradi"""
    current_time = time.time()
    for sub in subscriptions:
        if sub.get("user_id") == user_id and sub.get("active") and sub.get("end_date", 0) > current_time:
            return True
    return False


# ================== BOTDAN FOYDALANISH UCHUN KANAL TEKSHIRISH ==================
def check_subscription(bot, user_id, channels_file="channels.json"):
    """
    Foydalanuvchi barcha kanallarga obuna ekanligini tekshiradi.
    Agar obuna bo‘lmasa, ularni ro‘yxat sifatida qaytaradi.
    """
    not_subscribed = []
    channels = load_json(channels_file)
    for ch in channels:
        username = ch.get("username", ch.get("name", ""))
        if not username.startswith("@"):
            username = "@" + username
        try:
            member = bot.get_chat_member(username, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed.append(username)
        except Exception:
            not_subscribed.append(username)
    return not_subscribed
