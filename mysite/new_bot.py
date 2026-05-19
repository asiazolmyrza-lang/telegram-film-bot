import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from movies_data import MOVIES_DB, GENRES
from bot.models import TelegramUser, UserQuery, FavoriteMovie

TOKEN = "8713394605:AAFIz-uJIY3Kup4OACJT_J6Q9ZhnA1OUx00"
bot = TeleBot(TOKEN)

user_history = {}


def get_or_create_user(tg_user):
    user, _ = TelegramUser.objects.get_or_create(
        telegram_id=tg_user.id,
        defaults={
            'username': tg_user.username,
            'first_name': tg_user.first_name,
            'last_name': tg_user.last_name or '',
        }
    )
    return user


def save_query(user, cmd, detail=None):
    UserQuery.objects.create(user=user, command=cmd, details=detail)
    print(f"[SAVED] {user} - {cmd} - {detail}")


def menu():
    kb = InlineKeyboardMarkup(row_width=2)
    for g in GENRES:
        kb.add(InlineKeyboardButton(g.title(), callback_data=f"g_{g}"))
    kb.add(InlineKeyboardButton("🎲 Случайный", callback_data="rand"))
    kb.add(InlineKeyboardButton("⭐ Избранное", callback_data="favs"))
    return kb


def get_movie(uid, genre):
    if uid not in user_history:
        user_history[uid] = {}
    seen = user_history[uid].get(genre, [])
    avail = [m for m in MOVIES_DB.get(genre, []) if m not in seen]
    if not avail:
        return None
    m = random.choice(avail)
    user_history[uid].setdefault(genre, []).append(m)
    return m


@bot.message_handler(commands=['start'])
def start(m):
    u = get_or_create_user(m.from_user)
    save_query(u, 'start')
    user_history[u.telegram_id] = {}
    bot.send_message(m.chat.id, "🎬 Кино Бот\nВыбери жанр:", reply_markup=menu())


@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    u = get_or_create_user(c.from_user)
    data = c.data

    if data.startswith("g_"):
        genre = data[2:]
        movie = get_movie(u.telegram_id, genre)
        if not movie:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔄 Заново", callback_data=f"reset_{genre}"))
            kb.add(InlineKeyboardButton("🏠 Меню", callback_data="menu"))
            bot.edit_message_text(f"⚠️ В жанре {genre} фильмы кончились!", c.message.chat.id, c.message.message_id,
                                  reply_markup=kb)
            return
        save_query(u, 'genre', f"{genre}:{movie}")
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎲 Следующий", callback_data=f"g_{genre}"))
        kb.add(InlineKeyboardButton("👍 В избранное", callback_data=f"fav_{movie}"))
        kb.add(InlineKeyboardButton("🏠 Меню", callback_data="menu"))
        bot.edit_message_text(f"🎬 {genre.title()}\n\n{movie}", c.message.chat.id, c.message.message_id, reply_markup=kb)

    elif data.startswith("reset_"):
        genre = data[6:]
        if u.telegram_id in user_history:
            user_history[u.telegram_id][genre] = []
        movie = random.choice(MOVIES_DB[genre])
        user_history[u.telegram_id].setdefault(genre, []).append(movie)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎲 Следующий", callback_data=f"g_{genre}"))
        kb.add(InlineKeyboardButton("👍 В избранное", callback_data=f"fav_{movie}"))
        kb.add(InlineKeyboardButton("🏠 Меню", callback_data="menu"))
        bot.edit_message_text(f"🎬 {genre.title()} (начали заново)\n\n{movie}", c.message.chat.id, c.message.message_id,
                              reply_markup=kb)

    elif data.startswith("fav_"):
        movie = data[4:]
        FavoriteMovie.objects.get_or_create(user=u, movie_title=movie)
        save_query(u, 'favorite', movie)
        bot.answer_callback_query(c.id, f"✅ {movie} в избранном!")

    elif data == "rand":
        genre = random.choice(GENRES)
        movie = get_movie(u.telegram_id, genre)
        if not movie:
            user_history[u.telegram_id][genre] = []
            movie = random.choice(MOVIES_DB[genre])
            user_history[u.telegram_id][genre].append(movie)
        save_query(u, 'random', f"{genre}:{movie}")
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("👍 В избранное", callback_data=f"fav_{movie}"))
        kb.add(InlineKeyboardButton("🎲 Ещё", callback_data="rand"))
        kb.add(InlineKeyboardButton("🏠 Меню", callback_data="menu"))
        bot.edit_message_text(f"🎲 Случайный фильм\n\n{movie} ({genre})", c.message.chat.id, c.message.message_id,
                              reply_markup=kb)

    elif data == "favs":
        favs = FavoriteMovie.objects.filter(user=u)
        save_query(u, 'history')
        if not favs:
            txt = "⭐ Избранное пусто"
        else:
            txt = "⭐ Твои фильмы:\n" + "\n".join([f"• {f.movie_title}" for f in favs])
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Меню", callback_data="menu"))
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=kb)

    elif data == "menu":
        bot.edit_message_text("🎬 Главное меню", c.message.chat.id, c.message.message_id, reply_markup=menu())


if __name__ == "__main__":
    print("✅ БОТ С ИНТЕГРАЦИЕЙ DOCKER (DJANGO) ЗАПУЩЕН")
    print("📊 Данные сохраняются в БД")
    bot.infinity_polling()