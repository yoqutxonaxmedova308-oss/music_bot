import time
from functools import wraps
from typing import List, Dict, Any, Optional
from telebot import types

from utils import load_json, save_json, is_admin

# Default fayl yo'li — kerak bo'lsa set_anime_file orqali o'zgartiring
ANIME_FILE: str = "anime.json"
# Modul darajasida boshqariladigan adminlar ro'yxati — main.py dan set_admins orqali berilsin
ADMINS: List[int] = []


# ---------- Konfiguratsiya yordamchilari ----------
def set_anime_file(path: str) -> None:
    """ANIME_FILE yo'lini runtime-da o'zgartirish uchun."""
    global ANIME_FILE
    ANIME_FILE = path


def set_admins(admins_list: List[int]) -> None:
    """ADMINS ro'yxatini o'rnatadi (main fayldan chaqirilishi lozim)."""
    global ADMINS
    ADMINS = admins_list or []


# ---------- Decorator: admin tekshiruvi ----------
def admin_only(func):
    """Admin bo'lmagan foydalanuvchi chaqirsa xabar yuboradi.

    Eslatma: ADMINS modul darajasida set_admins orqali o'rnatilishi kerak.
    """

    @wraps(func)
    def wrapper(bot, message, *args, **kwargs):
        user_id = message.from_user.id
        if is_admin(user_id, ADMINS):
            return func(bot, message, *args, **kwargs)
        else:
            try:
                bot.send_message(message.chat.id, "❌ Sizda admin huquqi yo‘q!")
            except Exception:
                # Agar bot.send_message ham muammo bersa, tinch o'tamiz
                pass

    return wrapper


# ---------- Asosiy yordamchi funksiyalar ----------

def _load_anime_list() -> List[Dict[str, Any]]:
    data = load_json(ANIME_FILE)
    if not isinstance(data, list):
        return []
    return data


def _save_anime_list(data: List[Dict[str, Any]]) -> None:
    save_json(ANIME_FILE, data)


# ---------- Public API ----------

@admin_only
def list_anime(bot, message) -> None:
    """Adminlar uchun: mavjud anime ro'yxatini chiqaradi."""
    anime_list = _load_anime_list()
    if anime_list:
        lines = ["🎬 Anime ro'yxati:", ""]
        for i, a in enumerate(anime_list, start=1):
            name = a.get("name", "-")
            year = a.get("year", "Yil noma'lum")
            genre = a.get("genre", "-")
            lines.append(f"{i}. {name} ({year}) - {genre}")
        text = "\n".join(lines)
    else:
        text = "🎬 Hozircha anime mavjud emas."

    bot.send_message(message.chat.id, text)


def start_add_anime(bot, user_states: Dict[int, Dict[str, Any]], message) -> None:
    """Qo'shish jarayonini boshlaydi. user_states - tashqi dict bo'lishi kerak."""
    user_states[message.from_user.id] = {"step": "add_anime", "substep": "name", "data": {}}
    bot.send_message(message.chat.id, "➕ Anime nomini kiriting:")


def process_add_anime(bot, user_states: Dict[int, Dict[str, Any]], message) -> None:
    """Qo'shishning bosqichlarini boshqaradi. Har bosqichda message.text olinadi."""
    state = user_states.get(message.from_user.id)
    if not state or state.get("step") != "add_anime":
        return

    substep = state.get("substep")
    data = state.setdefault("data", {})

    try:
        if substep == "name":
            data["name"] = message.text.strip()
            state["substep"] = "image"
            bot.send_message(message.chat.id, "🖼 Anime rasm URL sini yuboring:")

        elif substep == "image":
            data["image"] = message.text.strip()
            state["substep"] = "genre"
            bot.send_message(message.chat.id, "🎭 Janrini kiriting:")

        elif substep == "genre":
            data["genre"] = message.text.strip()
            state["substep"] = "language"
            bot.send_message(message.chat.id, "🗣 Tilini kiriting:")

        elif substep == "language":
            data["language"] = message.text.strip()
            state["substep"] = "quality"
            bot.send_message(message.chat.id, "📺 Sifatini kiriting (mas: 1080p, 720p):")

        elif substep == "quality":
            data["quality"] = message.text.strip()
            state["substep"] = "year"
            bot.send_message(message.chat.id, "📆 Yilini kiriting (mas: 2023):")

        elif substep == "year":
            data["year"] = message.text.strip()
            data["id"] = int(time.time())
            data.setdefault("episodes", [])

            anime_list = _load_anime_list()
            anime_list.append(data)
            _save_anime_list(anime_list)

            bot.send_message(message.chat.id, f"✅ '{data.get('name','(nom yo‘q)')}' anime qo‘shildi!")
            # jarayon tugadi — state ni o'chirish
            user_states.pop(message.from_user.id, None)

    except Exception as e:
        # nimadir xato bo'lsa — xabar beramiz va state ni tozalaymiz
        try:
            bot.send_message(message.chat.id, "❌ Anime qo'shishda xatolik yuz berdi. Jarayon bekor qilindi.")
        except Exception:
            pass
        user_states.pop(message.from_user.id, None)


@admin_only
def remove_anime_step(bot, user_states: Dict[int, Dict[str, Any]], message) -> None:
    """O'chirish jarayonini boshlaydi: admindan o'chirmoqchi bo'lgan anime nomini so'raydi."""
    user_states[message.from_user.id] = {"step": "remove_anime"}
    bot.send_message(message.chat.id, "❌ O‘chirmoqchi bo‘lgan anime nomini kiriting:")


def process_remove_anime(bot, user_states: Dict[int, Dict[str, Any]], message) -> None:
    """O'chirish jarayonini davom ettiradi (user_states talab qilinadi)."""
    state = user_states.get(message.from_user.id)
    if not state or state.get("step") != "remove_anime":
        return

    anime_name = message.text.strip()
    anime_list = _load_anime_list()

    for anime in list(anime_list):
        if anime.get("name", "").lower() == anime_name.lower():
            anime_list.remove(anime)
            _save_anime_list(anime_list)
            bot.send_message(message.chat.id, f"✅ '{anime_name}' anime o‘chirildi!")
            user_states.pop(message.from_user.id, None)
            return

    bot.send_message(message.chat.id, "❌ Bunday anime topilmadi.")
    user_states.pop(message.from_user.id, None)


def search_anime(bot, message) -> None:
    """Foydalanuvchi yuborgan qidiruv so'rovi bo'yicha natijalarni qaytaradi."""
    query = message.text.strip().lower()
    anime_list = _load_anime_list()
    found = [a for a in anime_list if query in a.get('name', '').lower()]

    if found:
        lines = ["🔎 Qidiruv natijalari:", ""]
        for i, a in enumerate(found, start=1):
            lines.append(f"{i}. {a.get('name','-')} ({a.get('year','-')}) - {a.get('genre','-')}")
        text = "\n".join(lines)
    else:
        text = "🔎 Hech qanday natija topilmadi."

    bot.send_message(message.chat.id, text)


# ---------- Direct helper funksiyalar (kod ichidan chaqirish uchun) ----------

def add_anime(name: str, **kwargs) -> Dict[str, Any]:
    """To'g'ridan-to'g'ri anime qo'shish.

    Misol: add_anime('Naruto', year='2002', genre='Action')
    Returns: qo'shilgan obyektni qaytaradi.
    """
    anime_list = _load_anime_list()
    new_anime = {
        "id": int(time.time()),
        "name": name,
        "episodes": [],
    }
    # qo'shimcha maydonlar uchun kwargs dan foydalanamiz
    for k, v in kwargs.items():
        new_anime[k] = v

    anime_list.append(new_anime)
    _save_anime_list(anime_list)
    return new_anime


def remove_anime_by_name(name: str) -> bool:
    """Nomi bo'yicha anime o'chiradi. Agar o'chsa True qaytaradi, aks holda False."""
    anime_list = _load_anime_list()
    new_list = [a for a in anime_list if a.get('name','').lower() != name.lower()]
    if len(new_list) == len(anime_list):
        return False
    _save_anime_list(new_list)
    return True


def get_all_anime() -> List[Dict[str, Any]]:
    return _load_anime_list()


# End of file
