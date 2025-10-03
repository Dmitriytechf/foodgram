from django.contrib import admin

from .models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка тегов"""
    list_display = ('id', 'name', 'slug')
    list_display_links = ('name',)
    search_fields = ('name', 'slug')
    ordering = ('name',)
