# oldbot.py - простой бот для рекомендации фильмов

import random
from movies_data import MOVIES_DB, GENRES  # импорт фильмов


def get_movies_by_genre(genre):
    """Получить фильмы по жанру"""
    return MOVIES_DB.get(genre, [])


def get_random_movie():
    """Получить случайный фильм"""
    genre = random.choice(GENRES)
    movie = random.choice(MOVIES_DB[genre])
    return genre, movie


def main():
    """Консольная версия бота"""
    print("🎬 Добро пожаловать в Кино Бот!")
    print("Доступные жанры:", ", ".join(GENRES))
    print("Команды: /start, /help, /random, /genre [жанр], /exit")

    while True:
        command = input("\nВведите команду: ").strip().lower()

        if command == '/exit':
            print("До свидания!")
            break
        elif command == '/start':
            print("Бот запущен! Введите /help для списка команд")
        elif command == '/help':
            print(
                "Команды:\n/start - запуск\n/help - помощь\n/random - случайный фильм\n/genre [жанр] - фильмы по жанру\n/exit - выход")
        elif command == '/random':
            genre, movie = get_random_movie()
            print(f"🎲 Случайный фильм\nЖанр: {genre}\nФильм: {movie}")
        elif command.startswith('/genre'):
            parts = command.split()
            if len(parts) > 1:
                genre = parts[1]
                if genre in GENRES:
                    movies = get_movies_by_genre(genre)
                    print(f"🎬 Фильмы в жанре '{genre}':")
                    for i, movie in enumerate(movies[:10], 1):
                        print(f"{i}. {movie}")
                    if len(movies) > 10:
                        print(f"... и еще {len(movies) - 10} фильмов")
                else:
                    print(f"Жанр '{genre}' не найден. Доступны: {', '.join(GENRES)}")
            else:
                print("Укажите жанр. Пример: /genre комедия")
        else:
            print("Неизвестная команда. Введите /help")


if __name__ == "__main__":
    main()