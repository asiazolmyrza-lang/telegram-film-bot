from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import BroadcastMessage, AdminResponse, TelegramUser
import requests


def index(request):
    """Главная страница приложения (заглушка)"""
    return render(request, 'bot/index.html', {
        'title': 'Telegram Bot Admin Panel'
    })


@staff_member_required
def send_broadcast_api(request, broadcast_id):
    """API для отправки рассылки (вызывается из админки)"""
    try:
        broadcast = BroadcastMessage.objects.get(id=broadcast_id, status='sent')

        # Получаем всех активных пользователей
        users = TelegramUser.objects.filter(is_active=True)

        # Здесь будет вызов Telegram API
        # Пока просто заглушка
        broadcast.sent_at = timezone.now()
        broadcast.save()

        return JsonResponse({'status': 'ok', 'sent': users.count()})
    except BroadcastMessage.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Рассылка не найдена'})