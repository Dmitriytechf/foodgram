from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для подписок"""
    list_display = ('user', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email',
                     'author__username', 'author__email')
    ordering = ('-created_at',)


class CustomUserAdmin(UserAdmin):
    """Кастомная админка для пользователей с поиском по email и username"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
