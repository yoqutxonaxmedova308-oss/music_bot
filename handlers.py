# handlers.py
from telebot import types
from main import bot, USER_STATES, ADMINS, OWNER_ID
from utils import is_admin, check_subscription
from users import user_menu, handle_user_text, user_search_step
from admin import (
    admin_panel_menu, show_stats, add_admin_step, process_add_admin,
    remove_admin_step, process_remove_admin, channel_menu_step,
    process_add_channel, process_remove_channel, prepare_post,
    process_post_channel, process_broadcast_post, handle_admin_steps,
    start_add_anime, process_add_anime, process_remove_anime
)
from subscriptions import send_subscription_prompt

# /start handler
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    not_subs = check_subscription(bot, user_id)
    if not_subs:
        send_subscription_prompt(bot, message.chat.id, not_subs)
        return
    if is_admin(user_id, ADMINS):
        admin_panel_menu(bot, message)
    else:
        user_menu(bot, message)

# Universal "Orqaga" handler
@bot.message_handler(func=lambda m: m.text == "🔙 Orqaga")
def go_back_handler(message):
    user_id = message.from_user.id
    USER_STATES.pop(user_id, None)
    if is_admin(user_id, ADMINS):
        admin_panel_menu(bot, message)
    else:
        user_menu(bot, message)

# Foydalanuvchi bo‘limi
@bot.message_handler(func=lambda m: m.text in ["🔍 Anime izlash", "📖 Qo'llanma", "📢 Reklama va homiylik"])
def user_actions(message):
    handle_user_text(bot, message, USER_STATES, [])

@bot.message_handler(func=lambda m: USER_STATES.get(m.from_user.id, {}).get("step") == "user_search")
def user_search_messages(message):
    if message.text == "🔙 Orqaga":
        go_back_handler(message)
        return
    user_search_step(bot, message)
    USER_STATES.pop(message.from_user.id, None)

# Admin tez menyu tugmalari
@bot.message_handler(func=lambda m: m.text in [
    "📊 Statistikani ko‘rish", "➕ Admin qo‘shish", "❌ Admin o‘chirish",
    "📡 Kanal boshqaruvi", "📢 Xabar yuborish", "🎬 Anime boshqaruvi"
])
def admin_actions(message):
    if not is_admin(message.from_user.id, ADMINS):
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")
        return

    text = message.text
    if text == "📊 Statistikani ko‘rish":
        show_stats(bot, message)
    elif text == "➕ Admin qo‘shish":
        add_admin_step(bot, USER_STATES, message)
    elif text == "❌ Admin o‘chirish":
        remove_admin_step(bot, USER_STATES, message)
    elif text == "📡 Kanal boshqaruvi":
        channel_menu_step(bot, USER_STATES, message)
    elif text == "📢 Xabar yuborish":
        prepare_post(bot, USER_STATES, message)
    elif text == "🎬 Anime boshqaruvi":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Anime qo‘shish", "❌ Anime o‘chirish", "🔙 Orqaga")
        bot.send_message(message.chat.id, "🎬 Anime boshqaruvi:", reply_markup=markup)
        USER_STATES[message.from_user.id] = {"step": "anime_menu"}

# Anime qo‘shish va step handlerlari
@bot.message_handler(func=lambda m: m.text == "➕ Anime qo‘shish")
def add_anime(message):
    start_add_anime(bot, USER_STATES, message)

@bot.message_handler(func=lambda m: USER_STATES.get(m.from_user.id, {}).get("step") == "add_anime")
def handle_add_anime_step(message):
    process_add_anime(bot, USER_STATES, message)

@bot.message_handler(func=lambda m: USER_STATES.get(m.from_user.id, {}).get("step") == "remove_anime")
def handle_remove_anime_step(message):
    process_remove_anime(bot, USER_STATES, message)

# Admin-step processor (universal)
@bot.message_handler(func=lambda m: True)
def all_messages(message):
    state = USER_STATES.get(message.from_user.id)
    if not state:
        return

    step = state.get("step")
    if message.text == "🔙 Orqaga":
        go_back_handler(message)
        return

    if step == "add_admin":
        process_add_admin(bot, USER_STATES, ADMINS, message)
    elif step == "remove_admin":
        process_remove_admin(bot, USER_STATES, ADMINS, OWNER_ID, message)
    elif step == "add_channel":
        process_add_channel(bot, USER_STATES, message)
    elif step == "remove_channel":
        process_remove_channel(bot, USER_STATES, message)
    elif step == "add_anime":
        process_add_anime(bot, USER_STATES, message)
    elif step == "remove_anime":
        process_remove_anime(bot, USER_STATES, message)
    elif step == "broadcast_post":
        process_broadcast_post(bot, USER_STATES, message)
