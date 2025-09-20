# subscriptions.py
import time
from utils import load_json, save_json

SUBSCRIPTIONS_FILE = "subscriptions.json"
CHANNELS_FILE = "channels.json"

def get_subscriptions():
    data = load_json(SUBSCRIPTIONS_FILE)
    if isinstance(data, dict):
        return data.get("subscriptions", [])
    return data

def save_subscriptions(subs):
    data = load_json(SUBSCRIPTIONS_FILE)
    if not isinstance(data, dict):
        data = {}
    data["subscriptions"] = subs
    save_json(SUBSCRIPTIONS_FILE, data)

def is_subscribed_user(user_id):
    subs = get_subscriptions()
    current_time = time.time()
    for sub in subs:
        if sub.get("user_id") == user_id and sub.get("active") and sub.get("end_date", 0) > current_time:
            return True
    return False

def send_subscription_prompt(bot, chat_id, not_subscribed_channels):
    if not not_subscribed_channels:
        return
    text = "❌ Siz quyidagi kanallarga obuna bo‘lmadingiz:\n"
    text += "\n".join(not_subscribed_channels)
    text += "\n\n🔗 Iltimos, obuna bo‘ling va /start buyrug‘ini qayta bosing."
    bot.send_message(chat_id, text)

