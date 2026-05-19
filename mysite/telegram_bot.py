import os
import django
import random
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from movies_data import MOVIES_DB, GENRES
from bot.models import TelegramUser, UserQuery, FavoriteMovie

TOKEN = "8713394605:AAFIz-uJIY3Kup4OACJT_J6Q9ZhnA1OUx00"
bot = TeleBot(TOKEN)

user_temp_history = {}


def get_or_create_user(telegram_user):
    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_user.id,
        defaults={
            'username': telegram_user.username,
            'first_name': telegram_user.first_name,
            'last_name': telegram_user.last_name or '',
        }
    )
    return user


def save_query(user, command, details=None):
    UserQuery.objects.create(user=user, command=command, details=details)


def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    for genre in GENRES:
        keyboard.add(InlineKeyboardButton(f"🎬 {genre.title()}", callback_data=f"genre_{genre}"))
    keyboard.add(
        InlineKeyboardButton("🎲 Случайный фильм", callback_data="random"),
        InlineKeyboardButton("⭐ Избранное", callback_data="favorites")
    )
    keyboard.add(InlineKeyboardButton("❓ Помощь", callback_data="help"))
    keyboard.add(InlineKeyboardButton("💎 Поддержать проект", callback_data="donate"))
    return keyboard


def get_unseen_movie(user_id, genre):
    if user_id not in user_temp_history:
        user_temp_history[user_id] = {}
    shown = user_temp_history[user_id].get(genre, [])
    available = [m for m in MOVIES_DB.get(genre, []) if m not in shown]
    if not available:
        return None
    movie = random.choice(available)
    user_temp_history[user_id].setdefault(genre, []).append(movie)
    return movie


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_dj = get_or_create_user(message.from_user)
    save_query(user_dj, 'start')
    user_temp_history[user_dj.telegram_id] = {}
    bot.send_message(message.chat.id, "🎬 Добро пожаловать в Кино Бот!\nВыбери жанр кнопкой ниже:",
                     reply_markup=main_menu_keyboard())


@bot.message_handler(commands=['menu'])
def show_menu(message):
    user_dj = get_or_create_user(message.from_user)
    save_query(user_dj, 'menu')
    bot.send_message(message.chat.id, "🎬 Главное меню", reply_markup=main_menu_keyboard())


@bot.message_handler(commands=['history'])
def history_cmd(message):
    user_dj = get_or_create_user(message.from_user)
    save_query(user_dj, 'history')

    favorites = FavoriteMovie.objects.filter(user=user_dj)

    all_queries = UserQuery.objects.filter(user=user_dj).order_by('-created_at')[:20]

    text = "*⭐ Избранные фильмы:*\n"
    if favorites.exists():
        for fav in favorites:
            text += f"🎬 {fav.movie_title}\n"
    else:
        text += "Нет избранных фильмов\n"

    text += "\n*📜 Последние действия:*\n"
    for q in all_queries:
        text += f"• {q.get_command_display()}"
        if q.details:
            text += f" — {q.details[:30]}"
        text += f" ({q.created_at.strftime('%H:%M')})\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu_keyboard())


@bot.message_handler(commands=['random'])
def random_cmd(message):
    user_dj = get_or_create_user(message.from_user)
    genre = random.choice(GENRES)
    movie = get_unseen_movie(user_dj.telegram_id, genre)
    if movie is None:
        user_temp_history[user_dj.telegram_id][genre] = []
        movie = random.choice(MOVIES_DB[genre])
        user_temp_history[user_dj.telegram_id][genre].append(movie)
    save_query(user_dj, 'random', f"{genre} - {movie}")
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("👍 В избранное", callback_data=f"add_{movie}"))
    keyboard.add(InlineKeyboardButton("🎲 Ещё", callback_data=f"genre_{genre}"))
    keyboard.add(InlineKeyboardButton("🏠 Меню", callback_data="menu"))
    bot.send_message(message.chat.id, f"🎲 Случайный фильм\n\nЖанр: {genre}\nФильм: {movie}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_dj = get_or_create_user(call.from_user)

    if call.data.startswith('genre_'):
        genre = call.data.replace('genre_', '')
        movie = get_unseen_movie(user_dj.telegram_id, genre)
        if movie is None:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🔄 Начать заново", callback_data=f"reset_{genre}"))
            keyboard.add(InlineKeyboardButton("🔙 Назад в меню", callback_data="menu"))
            bot.edit_message_text(f"⚠️ *В жанре {genre.title()} закончились фильмы!*\nХочешь начать сначала?",
                                  call.message.chat.id, call.message.message_id, reply_markup=keyboard,
                                  parse_mode="Markdown")
            return
        save_query(user_dj, 'genre', f"{genre} - {movie}")
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🎲 Следующий фильм", callback_data=f"genre_{genre}"))
        keyboard.add(InlineKeyboardButton("👍 В избранное", callback_data=f"add_{movie}"))
        keyboard.add(InlineKeyboardButton("🏠 Меню", callback_data="menu"))
        bot.edit_message_text(f"🎬 *{genre.title()}*\n\n🎥 *Рекомендую:* {movie}", call.message.chat.id,
                              call.message.message_id, reply_markup=keyboard, parse_mode="Markdown")

    elif call.data.startswith('reset_'):
        genre = call.data.replace('reset_', '')
        if user_dj.telegram_id in user_temp_history:
            user_temp_history[user_dj.telegram_id][genre] = []
        movie = random.choice(MOVIES_DB[genre])
        user_temp_history[user_dj.telegram_id].setdefault(genre, []).append(movie)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🎲 Следующий фильм", callback_data=f"genre_{genre}"))
        keyboard.add(InlineKeyboardButton("👍 В избранное", callback_data=f"add_{movie}"))
        keyboard.add(InlineKeyboardButton("🏠 Меню", callback_data="menu"))
        bot.edit_message_text(f"🎬 *{genre.title()}* (начали заново)\n\n🎥 *Рекомендую:* {movie}", call.message.chat.id,
                              call.message.message_id, reply_markup=keyboard, parse_mode="Markdown")

    elif call.data == "random":
        genre = random.choice(GENRES)
        movie = get_unseen_movie(user_dj.telegram_id, genre)
        if movie is None:
            user_temp_history[user_dj.telegram_id][genre] = []
            movie = random.choice(MOVIES_DB[genre])
            user_temp_history[user_dj.telegram_id][genre].append(movie)
        save_query(user_dj, 'random', f"{genre} - {movie}")
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("👍 В избранное", callback_data=f"add_{movie}"))
        keyboard.add(InlineKeyboardButton("🎲 Ещё", callback_data=f"genre_{genre}"))
        keyboard.add(InlineKeyboardButton("🏠 Меню", callback_data="menu"))
        bot.edit_message_text(f"🎲 Случайный фильм\n\nЖанр: {genre}\nФильм: {movie}", call.message.chat.id,
                              call.message.message_id, reply_markup=keyboard)

    elif call.data.startswith('add_'):
        movie = call.data.replace('add_', '')
        fav, created = FavoriteMovie.objects.get_or_create(user=user_dj, movie_title=movie)
        if created:
            for genre, movies in MOVIES_DB.items():
                if movie in movies:
                    fav.genre = genre
                    fav.save()
                    break
            save_query(user_dj, 'favorite', movie)
            bot.answer_callback_query(call.id, f"✅ {movie} добавлен в избранное!", show_alert=False)
        else:
            bot.answer_callback_query(call.id, f"📌 {movie} уже в избранном!", show_alert=False)

    elif call.data == "favorites":
        favorites = FavoriteMovie.objects.filter(user=user_dj)
        save_query(user_dj, 'other', 'Просмотр избранного')
        if not favorites.exists():
            text = "⭐ *Избранное*\n\nУ вас пока нет избранных фильмов.\nДобавьте фильм 👍!"
        else:
            text = "*⭐ Твои избранные фильмы:*\n\n"
            for fav in favorites:
                text += f"🎬 {fav.movie_title}"
                if fav.genre:
                    text += f" *({fav.genre})*"
                text += "\n"
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Назад в меню", callback_data="menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard,
                              parse_mode="Markdown")

    elif call.data == "donate":
        save_query(user_dj, 'other', 'Открыл платежи')
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Назад в меню", callback_data="menu"))
        keyboard.add(InlineKeyboardButton("💎 Поддержать (заглушка)", callback_data="fake_payment"))
        bot.edit_message_text(
            "💎 *Поддержать проект*\n\nЭто демо-версия платежей.\nВ реальном проекте здесь была бы интеграция с платежной системой.\n\nСпасибо за интерес! 🎬",
            call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode="Markdown")

    elif call.data == "fake_payment":
        bot.answer_callback_query(call.id, "🔧 Это демо-заглушка платежей. Спасибо!", show_alert=True)

    elif call.data == "help":
        save_query(user_dj, 'help')
        help_text = """❓ *Помощь*\n\n/start - Главное меню\n/menu - Показать меню\n/random - Случайный фильм\n/history - Мои избранные фильмы\n\nИспользуй кнопки для выбора жанра и добавления в избранное!"""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Назад в меню", callback_data="menu"))
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=keyboard,
                              parse_mode="Markdown")

    elif call.data == "menu":
        bot.edit_message_text("🎬 Главное меню\nВыбери жанр:", call.message.chat.id, call.message.message_id,
                              reply_markup=main_menu_keyboard())
        check_admin_responses(user_dj, call.message.chat.id)

@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    bot.reply_to(message, "❌ Неизвестная команда.\n\nДоступные команды:\n/start - Главное меню\n/menu - Меню\n/random - Случайный фильм\n/history - Избранное\n/help - Помощь")

def check_admin_responses(user_dj, chat_id):
    responses = AdminResponse.objects.filter(user=user_dj, is_sent=False)
    for response in responses:
        bot.send_message(chat_id, f"📩 *Ответ от администратора:*\n\n{response.response_text}", parse_mode="Markdown")
        response.is_sent = True
        response.sent_at = datetime.now()
        response.save()

import threading
import time

def check_responses_loop():
    while True:
        time.sleep(3)
        try:
            from bot.models import AdminResponse
            responses = AdminResponse.objects.filter(is_sent=False)
            for response in responses:
                try:
                    bot.send_message(
                        response.user.telegram_id,
                        f"📩 *Ответ от администратора:*\n\n{response.response_text}",
                        parse_mode="Markdown"
                    )
                    response.is_sent = True
                    response.sent_at = datetime.now()
                    response.save()
                    print(f"✅ Ответ отправлен {response.user}")
                except:
                    pass
        except:
            pass

if __name__ == "__main__":
    print("Бот запущен с интеграцией с Django")
    # Запускаем фоновый поток для проверки ответов
    thread = threading.Thread(target=check_responses_loop, daemon=True)
    thread.start()
    bot.infinity_polling()