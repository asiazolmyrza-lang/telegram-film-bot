# 🎬 Кино Бот — Telegram бот для рекомендации фильмов

## Описание проекта

Telegram-бот помогает пользователям выбирать фильмы по 12 жанрам. Бот рекомендует фильмы, которые пользователь ещё не видел, позволяет добавлять их в избранное и просматривать историю.

**Особенность:** Все действия пользователей сохраняются в Django админ-панель.

## Используемые технологии

- Python 3.9
- Django 4.2
- pyTelegramBotAPI
- SQLite3

## Функции бота

- ✅ 12 жанров фильмов
- ✅ Случайный фильм
- ✅ Добавление в избранное
- ✅ Просмотр избранного
- ✅ Админ-панель Django
- ✅ Демо-платежи

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/menu` | Показать меню |
| `/random` | Случайный фильм |
| `/history` | Избранные фильмы |
| `/help` | Помощь |

## Установка и запуск

```bash
git clone https://github.com/asiazolmyrza-lang/telegram-film-bot
cd mysite
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python telegram_bot.py
```
Скриншоты
https://screenshots/menu.png
https://screenshots/recommend.png
https://screenshots/favorites.png
https://screenshots/admin.png
https://screenshots/random.png
https://screenshots/help.png
https://screenshots/donate.png
https://screenshots/history.png
