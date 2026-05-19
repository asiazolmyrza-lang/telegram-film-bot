from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from .models import TelegramUser, UserQuery, FavoriteMovie, BroadcastMessage, Reminder, AdminResponse


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'username', 'first_name', 'registered_at', 'is_active']
    list_filter = ['is_active', 'registered_at']
    search_fields = ['telegram_id', 'username', 'first_name']
    list_editable = ['is_active']


@admin.register(UserQuery)
class UserQueryAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_command_display', 'details_short', 'created_at', 'reply_button']
    list_filter = ['command', 'created_at']
    search_fields = ['user__username', 'user__telegram_id', 'details']
    readonly_fields = ['user', 'command', 'details', 'created_at']

    def details_short(self, obj):
        return obj.details[:50] + '...' if obj.details and len(obj.details) > 50 else obj.details

    details_short.short_description = "Детали"

    def reply_button(self, obj):
        url = reverse('admin:bot_adminresponse_add')
        return format_html(
            '<a class="button" href="{}?user={}" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">✉️ Ответить</a>',
            url, obj.user.id)

    reply_button.short_description = "Ответ"
    reply_button.allow_tags = True


@admin.register(FavoriteMovie)
class FavoriteMovieAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie_title', 'genre', 'added_at']
    list_filter = ['genre', 'added_at']
    search_fields = ['user__username', 'movie_title']


@admin.register(BroadcastMessage)
class BroadcastMessageAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'created_at', 'sent_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'message_text']
    readonly_fields = ['created_at', 'sent_at']
    actions = ['send_broadcast']

    def send_broadcast(self, request, queryset):
        for msg in queryset:
            if msg.status == 'draft':
                msg.status = 'sent'
                msg.save()
        self.message_user(request, f"Отправлено {queryset.count()} рассылок")

    send_broadcast.short_description = "Отправить выбранные рассылки"


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['user', 'text_short', 'remind_at', 'is_sent']
    list_filter = ['is_sent', 'remind_at']
    search_fields = ['user__username', 'text']

    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_short.short_description = "Текст"


@admin.register(AdminResponse)
class AdminResponseAdmin(admin.ModelAdmin):
    list_display = ['user', 'response_short', 'is_sent', 'created_at']
    list_filter = ['is_sent', 'created_at']
    search_fields = ['user__username', 'response_text']

    def response_short(self, obj):
        return obj.response_text[:50] + '...' if len(obj.response_text) > 50 else obj.response_text

    response_short.short_description = "Ответ"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        user_id = request.GET.get('user')
        if user_id:
            try:
                user = TelegramUser.objects.get(id=user_id)
                form.base_fields['user'].initial = user
                form.base_fields['user'].disabled = True
            except TelegramUser.DoesNotExist:
                pass
        return form

    def response_change(self, request, obj):
        return redirect('/admin/bot/userquery/')

    def response_add(self, request, obj, post_url_continue=None):
        return redirect('/admin/bot/userquery/')