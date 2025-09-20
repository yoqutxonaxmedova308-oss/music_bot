# admin.py
import time
from telebot import types
from utils import load_json, save_json, is_admin, check_subscription
from anime import start_add_anime, process_add_anime, process_remove_anime
from subscriptions import send_subscription_prompt, SUBSCRIPTIONS_FILE, CHANNELS_FILE

ANIME_FILE = "anime.json"
CHANNELS_FILE = "channels.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"

def admin_panel_menu(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Statistikani ko‘rish", "➕ Admin qo‘shish")
    markup.add("❌ Admin o‘chirish", "🎬 Anime boshqaruvi")
    markup.add("📡 Kanal boshqaruvi", "📢 Xabar yuborish")
    markup.add("🔙 Orqaga")
    bot.send_message(message.chat.id, "🛠 Admin panel:", reply_markup=markup)

def show_stats(bot, message):
    anime_list = load_json(ANIME_FILE)
    channels = load_json(CHANNELS_FILE)
    subs = load_json(SUBSCRIPTIONS_FILE)
    text = (
        f"📊 Statistika:\n"
        f"• Anime soni: {len(anime_list)}\n"
        f"• Kanal soni: {len(channels)}\n"
        f"• Obunachilar: {len(subs) if isinstance(subs, list) else len(subs.get('subscriptions', []))}"
    )
    bot.send_message(message.chat.id, text)

def add_admin_step(bot, USER_STATES, message):
    USER_STATES[message.from_user.id] = {"step": "add_admin"}
    bot.send_message(message.chat.id, "➕ Yangi adminning ID sini kiriting:")

def process_add_admin(bot, USER_STATES, ADMINS, message):
    try:
        new_admin = int(message.text.strip())
        if new_admin not in ADMINS:
            ADMINS.append(new_admin)
            bot.send_message(message.chat.id, f"✅ Admin qo‘shildi: {new_admin}")
        else:
            bot.send_message(message.chat.id, "❗️ Bu ID allaqachon admin.")
    except Exception:
        bot.send_message(message.chat.id, "❌ Noto‘g‘ri ID.")
    USER_STATES.pop(message.from_user.id, None)

def remove_admin_step(bot, USER_STATES, message):
    USER_STATES[message.from_user.id] = {"step": "remove_admin"}
    bot.send_message(message.chat.id, "❌ O‘chirmoqchi bo‘lgan admin ID sini kiriting:")

def process_remove_admin(bot, USER_STATES, ADMINS, OWNER_ID, message):
    try:
        admin_id = int(message.text.strip())
        if admin_id == OWNER_ID:
            bot.send_message(message.chat.id, "❌ Ownerni o‘chira olmaysiz!")
        elif admin_id in ADMINS:
            ADMINS.remove(admin_id)
            bot.send_message(message.chat.id, f"✅ Admin o‘chirildi: {admin_id}")
        else:
            bot.send_message(message.chat.id, "❗️ Bunday admin yo‘q.")
    except Exception:
        bot.send_message(message.chat.id, "❌ Noto‘g‘ri ID.")
    USER_STATES.pop(message.from_user.id, None)

def anime_menu_step(bot, USER_STATES, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Anime qo‘shish", "❌ Anime o‘chirish")
    markup.add("🔙 Orqaga")
    USER_STATES[message.from_user.id] = {"step": "anime_menu"}
    bot.send_message(message.chat.id, "🎬 Anime boshqaruvi:", reply_markup=markup)

def handle_anime_steps(bot, USER_STATES, message):
    step = USER_STATES[message.from_user.id]["step"]
    text = message.text
    anime_list = load_json(ANIME_FILE)

    if step == "anime_menu":
        if text == "➕ Anime qo‘shish":
            USER_STATES[message.from_user.id]["step"] = "add_anime"
            bot.send_message(message.chat.id, "➕ Qo‘shmoqchi bo‘lgan anime nomini kiriting:")
        elif text == "❌ Anime o‘chirish":
            USER_STATES[message.from_user.id]["step"] = "remove_anime_step"
            bot.send_message(message.chat.id, "❌ O‘chirmoqchi bo‘lgan anime nomini kiriting:")
    elif step == "add_anime":
        anime_list.append({"name": text})
        save_json(ANIME_FILE, anime_list)
        bot.send_message(message.chat.id, f"✅ Anime '{text}' qo‘shildi!")
        anime_menu_step(bot, USER_STATES, message)
    elif step == "remove_anime_step":
        anime = next((a for a in anime_list if a["name"] == text), None)
        if anime:
            anime_list.remove(anime)
            save_json(ANIME_FILE, anime_list)
            bot.send_message(message.chat.id, f"❌ Anime '{text}' o‘chirildi!")
        else:
            bot.send_message(message.chat.id, "❌ Anime topilmadi.")
        anime_menu_step(bot, USER_STATES, message)

# --- KANAL BOSHQARUV ---
def channel_menu_step(bot, USER_STATES, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Kanal qo‘shish", "❌ Kanal o‘chirish", "🔙 Orqaga")
    bot.send_message(message.chat.id, "📡 Kanal boshqaruvi:", reply_markup=markup)
    USER_STATES[message.from_user.id] = {"step": "channel_menu"}

def handle_channel_steps(bot, USER_STATES, message):
    step = USER_STATES[message.from_user.id]["step"]
    text = message.text
    channels = load_json(CHANNELS_FILE)

    if step == "channel_menu":
        if text == "➕ Kanal qo‘shish":
            USER_STATES[message.from_user.id]["step"] = "add_channel"
            bot.send_message(message.chat.id, "➕ Qo‘shmoqchi bo‘lgan kanal nomini kiriting:")
        elif text == "❌ Kanal o‘chirish":
            USER_STATES[message.from_user.id]["step"] = "remove_channel"
            bot.send_message(message.chat.id, "❌ O‘chirmoqchi bo‘lgan kanal nomini kiriting:")
    elif step == "add_channel":
        channels.append({"name": text})
        save_json(CHANNELS_FILE, channels)
        bot.send_message(message.chat.id, f"✅ Kanal '{text}' qo‘shildi!")
        channel_menu_step(bot, USER_STATES, message)
    elif step == "remove_channel":
        channel = next((ch for ch in channels if ch["name"] == text), None)
        if channel:
            channels.remove(channel)
            save_json(CHANNELS_FILE, channels)
            bot.send_message(message.chat.id, f"❌ Kanal '{text}' o‘chirildi!")
        else:
            bot.send_message(message.chat.id, "❌ Kanal topilmadi.")
        channel_menu_step(bot, USER_STATES, message)

# --- POST YUBORISH ---
def prepare_post(bot, USER_STATES, message):
    USER_STATES[message.from_user.id] = {"step": "broadcast_post"}
    bot.send_message(message.chat.id, "📢 Yuboriladigan xabar matnini kiriting:")

def process_broadcast_post(bot, USER_STATES, message):
    state = USER_STATES.get(message.from_user.id)
    if not state or state.get("step") != "broadcast_post":
        return
    channel = state.get("channel")
    users_list = load_json(SUBSCRIPTIONS_FILE)
    count = 0
    for u in users_list:
        if u.get("active") and u.get("end_date", 0) > time.time():
            try:
                bot.send_message(u["user_id"], message.text)
                count += 1
            except:
                continue
    bot.send_message(message.chat.id, f"✅ Post {channel['name']} kanali foydalanuvchilariga yuborildi! ({count} ta foydalanuvchi)")
    USER_STATES.pop(message.from_user.id, None)

# --- BOSHQA FUNKSIYALAR ---
def handle_admin_steps(bot, USER_STATES, ADMINS, OWNER_ID, message):
    # Bu universal step handler, agar kerak bo‘lsa
    pass

def start_add_anime(bot, USER_STATES, message):
    USER_STATES[message.from_user.id] = {"step": "add_anime", "substep": "name", "data": {}}
    bot.send_message(message.chat.id, "➕ Anime nomini kiriting:")

def process_add_anime(bot, USER_STATES, message):
    # ...anime qo‘shish bosqichlari...
    pass

def process_remove_anime(bot, USER_STATES, message):
    # ...anime o‘chirish bosqichlari...
    pass

