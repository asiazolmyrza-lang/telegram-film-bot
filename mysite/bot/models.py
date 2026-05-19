from django.db import models


class TelegramUser(models.Model):
    """Telegram-пользователи"""
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=100, blank=True, null=True, verbose_name="Username")
    first_name = models.CharField(max_length=100, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Фамилия")
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    def __str__(self):
        return f"@{self.username or self.telegram_id}"

    class Meta:
        verbose_name = "Telegram пользователь"
        verbose_name_plural = "Telegram пользователи"


class UserQuery(models.Model):
    """Запросы/команды от пользователей"""
    COMMAND_CHOICES = [
        ('start', '/start'),
        ('menu', '/menu'),
        ('random', '/random'),
        ('help', '/help'),
        ('history', '/history'),
        ('genre', 'Выбор жанра'),
        ('favorite', 'В избранное'),
        ('other', 'Другое'),
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='queries')
    command = models.CharField(max_length=50, choices=COMMAND_CHOICES, verbose_name="Команда")
    details = models.TextField(blank=True, null=True, verbose_name="Детали")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время запроса")

    def __str__(self):
        return f"{self.user} - {self.get_command_display()}"

    class Meta:
        ordering = ['-created_at']


class FavoriteMovie(models.Model):
    """Избранные фильмы"""
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='favorites')
    movie_title = models.CharField(max_length=200, verbose_name="Название фильма")
    genre = models.CharField(max_length=50, blank=True, null=True, verbose_name="Жанр")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        unique_together = ['user', 'movie_title']

    def __str__(self):
        return f"{self.user} → {self.movie_title}"


class BroadcastMessage(models.Model):
    """Массовые рассылки"""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('sent', 'Отправлено'),
        ('scheduled', 'Запланировано'),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    message_text = models.TextField(verbose_name="Текст сообщения")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_time = models.DateTimeField(blank=True, null=True, verbose_name="Время отправки")
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title


class Reminder(models.Model):
    """Напоминания"""
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='reminders')
    text = models.CharField(max_length=500, verbose_name="Текст")
    remind_at = models.DateTimeField(verbose_name="Время напоминания")
    is_sent = models.BooleanField(default=False, verbose_name="Отправлено")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.remind_at.strftime('%d.%m %H:%M')}"


class AdminResponse(models.Model):
    """Ответы админа пользователям"""
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='admin_responses')
    response_text = models.TextField(verbose_name="Текст ответа")
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Ответ для {self.user}"