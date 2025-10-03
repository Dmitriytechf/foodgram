from django.contrib import admin

from .models import Ingredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка ингредиентов"""
    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
